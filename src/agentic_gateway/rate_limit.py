"""LLM-aware token-bucket rate limiting primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic


@dataclass
class TokenBucket:
    """A simple token bucket keyed by estimated LLM/tool-call cost."""

    capacity: float
    refill_rate_per_second: float
    tokens: float | None = None
    updated_at: float = field(default_factory=monotonic)

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        if self.refill_rate_per_second < 0:
            raise ValueError("refill_rate_per_second cannot be negative")
        if self.tokens is None:
            self.tokens = self.capacity

    def allow(self, cost: float = 1.0) -> bool:
        """Return whether a request with the provided cost can proceed."""

        if cost <= 0:
            raise ValueError("cost must be positive")
        self._refill()
        if self.tokens is None or self.tokens < cost:
            return False
        self.tokens -= cost
        return True

    def _refill(self) -> None:
        now = monotonic()
        elapsed = max(0.0, now - self.updated_at)
        self.updated_at = now
        current = self.tokens if self.tokens is not None else self.capacity
        self.tokens = min(self.capacity, current + elapsed * self.refill_rate_per_second)
