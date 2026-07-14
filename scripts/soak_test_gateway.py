#!/usr/bin/env python3
"""Run a lightweight soak test against the subprocess sandbox lifecycle."""

from __future__ import annotations

import argparse
import tracemalloc

from agentic_gateway import AgenticGateway, TokenBucket, ToolCall

SNIPPETS = [
    "print(sum(range(20)))",
    "import math\nprint(round(math.sqrt(144)))",
    "print('sandbox-ok')",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100)
    args = parser.parse_args()

    gateway = AgenticGateway(TokenBucket(capacity=args.iterations + 1, refill_rate_per_second=0))
    tracemalloc.start()
    for index in range(args.iterations):
        code = SNIPPETS[index % len(SNIPPETS)]
        [result] = gateway.execute([ToolCall(code=code, call_id=f"soak-{index}")])
        if result.status != "completed":
            raise SystemExit(f"call {index} failed: {result.error}")
    current, peak = tracemalloc.get_traced_memory()
    print(gateway.metrics.to_prometheus(), end="")
    print(f"agentic_gateway_soak_memory_current_bytes {current}")
    print(f"agentic_gateway_soak_memory_peak_bytes {peak}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
