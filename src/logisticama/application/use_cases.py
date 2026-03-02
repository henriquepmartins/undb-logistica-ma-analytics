from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from logisticama.application.dto import DashboardSummary, QueryWindow
from logisticama.domain.ports import QueryRepository, TimeRangeQuery
from logisticama.shared.time_utils import parse_iso_to_epoch_seconds


class QueryLogisticsDashboard:
    def __init__(self, repository: QueryRepository) -> None:
        self._repository = repository

    def build_summary(self, window: QueryWindow) -> DashboardSummary:
        summary = self._repository.summarize_window(self._to_query(window))
        delayed_share = 0.0
        if summary["total_events"]:
            delayed_share = summary["delayed_events"] / summary["total_events"]
        return DashboardSummary(
            total_events=int(summary["total_events"]),
            delayed_events=int(summary["delayed_events"]),
            average_delay=float(summary["average_delay"]),
            delayed_share=float(delayed_share),
            max_delay=int(summary["max_delay"]),
        )

    def count_delays(self, window: QueryWindow) -> int:
        return self._repository.count_delays(self._to_query(window))

    def chart_frame(self) -> pd.DataFrame:
        return self._repository.events_frame().copy()

    @staticmethod
    def summary_to_dict(summary: DashboardSummary) -> dict[str, float | int]:
        return asdict(summary)

    @staticmethod
    def _to_query(window: QueryWindow) -> TimeRangeQuery:
        return TimeRangeQuery(
            start_ts=parse_iso_to_epoch_seconds(window.start_iso),
            end_ts=parse_iso_to_epoch_seconds(window.end_iso),
            min_delay=window.min_delay,
            hub=window.hub,
            status=window.status,
        )

