import json
import unittest

from agentic_gateway import AgenticGateway, PythonSandbox, TokenBucket, ToolCall
from agentic_gateway.sandbox import SandboxViolation


class GatewayTests(unittest.TestCase):
    def test_executes_safe_python(self):
        gateway = AgenticGateway(TokenBucket(capacity=5, refill_rate_per_second=0))

        [result] = gateway.execute([ToolCall(code="print(2 + 2)", call_id="c1")])

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output.strip(), "4")
        self.assertIn("completed", [log.event for log in gateway.logs])
        self.assertEqual(gateway.metrics.completed_calls, 1)

    def test_blocks_when_rate_limited(self):
        gateway = AgenticGateway(TokenBucket(capacity=1, refill_rate_per_second=0))

        first, second = gateway.execute([
            ToolCall(code="print('a')", call_id="c1"),
            ToolCall(code="print('b')", call_id="c2"),
        ])

        self.assertEqual(first.status, "completed")
        self.assertEqual(second.status, "blocked")
        self.assertEqual(second.error, "rate limited")
        self.assertEqual(gateway.metrics.rate_limit_drops, 1)

    def test_sandbox_blocks_file_access(self):
        sandbox = PythonSandbox()

        with self.assertRaises(SandboxViolation):
            sandbox.run("open('/etc/passwd').read()")

    def test_gateway_batches_by_service(self):
        gateway = AgenticGateway(TokenBucket(capacity=5, refill_rate_per_second=0))

        gateway.execute([
            ToolCall(code="print('x')", call_id="c1"),
            ToolCall(code="print('y')", call_id="c2"),
        ])

        batch_events = [log for log in gateway.logs if log.event == "batch_started"]
        self.assertEqual(batch_events[0].metadata["size"], 2)

    def test_logs_are_json_serializable(self):
        gateway = AgenticGateway(TokenBucket(capacity=5, refill_rate_per_second=0))

        gateway.execute([ToolCall(code="print('json')", call_id="json-call")])

        completed_log = next(log for log in gateway.logs if log.event == "completed")
        encoded = completed_log.to_json()
        decoded = json.loads(encoded)
        self.assertEqual(decoded["event"], "completed")
        self.assertEqual(decoded["call_id"], "json-call")
        self.assertIn("agentic_gateway_completed_calls_total", gateway.metrics.to_prometheus())


if __name__ == "__main__":
    unittest.main()
