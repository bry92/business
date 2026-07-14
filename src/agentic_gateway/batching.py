"""Basic request batching and deduplication utilities."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def group_by_key(items: Iterable[T], key_name: str) -> dict[str, list[T]]:
    """Group dataclass-like items by a named attribute."""

    grouped: dict[str, list[T]] = defaultdict(list)
    for item in items:
        grouped[str(getattr(item, key_name))].append(item)
    return dict(grouped)
