from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogisticsEvent:
    package_id: str
    timestamp: int
    status: str
    hub: str
    delay_minutes: int

