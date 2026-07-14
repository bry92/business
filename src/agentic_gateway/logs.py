"""Structured execution logs and lightweight metrics for gateway decisions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from time import time
from typing import Any


@dataclass(frozen=True)
class ExecutionLog:
    """JSON-serializable event record for observability pipelines."""

    event: str
    call_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time)

    def to_json(self) -> str:
        """Return a compact JSON log line for Fluentd-style collectors."""

        return json.dumps(asdict(self), separators=(",", ":"), sort_keys=True)


@dataclass
class GatewayMetrics:
    """In-memory counters suitable for exporting to Prometheus text format."""

    completed_calls: int = 0
    failed_calls: int = 0
    rate_limit_drops: int = 0
    sandbox_token_cost: float = 0.0
    total_execution_duration_ms: float = 0.0

    def record_completed(self, duration_ms: float, token_cost: float) -> None:
        self.completed_calls += 1
        self.sandbox_token_cost += token_cost
        self.total_execution_duration_ms += duration_ms

    def record_failed(self, duration_ms: float, token_cost: float) -> None:
        self.failed_calls += 1
        self.sandbox_token_cost += token_cost
        self.total_execution_duration_ms += duration_ms

    def record_rate_limit_drop(self) -> None:
        self.rate_limit_drops += 1

    def to_prometheus(self) -> str:
        """Render metrics in Prometheus text exposition format."""

        values = {
            "agentic_gateway_completed_calls_total": self.completed_calls,
            "agentic_gateway_failed_calls_total": self.failed_calls,
            "agentic_gateway_rate_limit_drops_total": self.rate_limit_drops,
            "agentic_gateway_sandbox_token_cost_total": self.sandbox_token_cost,
            "agentic_gateway_execution_duration_ms_total": self.total_execution_duration_ms,
        }
        return "\n".join(f"{name} {value}" for name, value in values.items()) + "\n"
