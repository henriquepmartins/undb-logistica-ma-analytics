from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd


@dataclass(frozen=True, slots=True)
class TimeRangeQuery:
    start_ts: int
    end_ts: int
    min_delay: int = 30
    hub: str | None = None
    status: str | None = None


class LogSource(Protocol):
    def load(self) -> pd.DataFrame:
        """Return a normalized dataframe of events."""


class QueryRepository(Protocol):
    def count_delays(self, query: TimeRangeQuery) -> int:
        """Count delayed events in the given range."""

    def summarize_window(self, query: TimeRangeQuery) -> dict[str, float | int]:
        """Return summary metrics for a range."""

    def events_frame(self) -> pd.DataFrame:
        """Return the normalized event frame for charting."""

