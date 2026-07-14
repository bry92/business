"""Agentic tool-call gateway prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from time import perf_counter
from uuid import uuid4

from .batching import group_by_key
from .logs import ExecutionLog, GatewayMetrics
from .rate_limit import TokenBucket
from .sandbox import PythonSandbox, SandboxViolation

Status = Literal["completed", "blocked", "failed"]


@dataclass(frozen=True)
class ToolCall:
    """Canonical request envelope for a gateway-managed tool call."""

    code: str
    agent_id: str = "default-agent"
    service: str = "python"
    cost: float = 1.0
    call_id: str = ""

    def normalized_id(self) -> str:
        return self.call_id or str(uuid4())


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    status: Status
    output: str = ""
    error: str = ""


class AgenticGateway:
    """Coordinate sandboxing, rate limits, batching, and execution logs."""

    def __init__(self, bucket: TokenBucket, sandbox: PythonSandbox | None = None) -> None:
        self.bucket = bucket
        self.sandbox = sandbox or PythonSandbox()
        self.logs: list[ExecutionLog] = []
        self.metrics = GatewayMetrics()

    def execute(self, calls: list[ToolCall]) -> list[ToolResult]:
        """Execute a batch of tool calls and return ordered results."""

        results: list[ToolResult] = []
        for service, grouped_calls in group_by_key(calls, "service").items():
            self._log("batch_started", service, {"size": len(grouped_calls)})
            for call in grouped_calls:
                results.append(self._execute_one(call))
            self._log("batch_completed", service, {"size": len(grouped_calls)})
        return results

    def _execute_one(self, call: ToolCall) -> ToolResult:
        call_id = call.normalized_id()
        if call.service != "python":
            self._log("blocked", call_id, {"reason": "unsupported_service", "service": call.service})
            return ToolResult(call_id=call_id, status="blocked", error="unsupported service")
        if not self.bucket.allow(call.cost):
            self.metrics.record_rate_limit_drop()
            self._log("blocked", call_id, {"reason": "rate_limited", "cost": call.cost})
            return ToolResult(call_id=call_id, status="blocked", error="rate limited")
        self._log("started", call_id, {"agent_id": call.agent_id, "cost": call.cost})
        started_at = perf_counter()
        try:
            output = self.sandbox.run(call.code)
        except (SandboxViolation, TimeoutError) as exc:
            duration_ms = (perf_counter() - started_at) * 1000
            self.metrics.record_failed(duration_ms=duration_ms, token_cost=call.cost)
            self._log("failed", call_id, {"duration_ms": duration_ms, "error": str(exc)})
            return ToolResult(call_id=call_id, status="failed", error=str(exc))
        duration_ms = (perf_counter() - started_at) * 1000
        self.metrics.record_completed(duration_ms=duration_ms, token_cost=call.cost)
        self._log("completed", call_id, {"duration_ms": duration_ms, "output_bytes": len(output.encode())})
        return ToolResult(call_id=call_id, status="completed", output=output)

    def _log(self, event: str, call_id: str, metadata: dict[str, object]) -> None:
        self.logs.append(ExecutionLog(event=event, call_id=call_id, metadata=metadata))
