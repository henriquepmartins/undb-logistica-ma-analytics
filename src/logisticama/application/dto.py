from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueryWindow:
    start_iso: str
    end_iso: str
    min_delay: int = 30
    hub: str | None = None
    status: str | None = None


@dataclass(frozen=True, slots=True)
class DashboardSummary:
    total_events: int
    delayed_events: int
    average_delay: float
    delayed_share: float
    max_delay: int

