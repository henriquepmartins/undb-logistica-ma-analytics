from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from logisticama.domain.ports import QueryRepository, TimeRangeQuery


@dataclass(frozen=True, slots=True)
class SliceIndex:
    timestamps: np.ndarray
    delays: np.ndarray
    delayed_30_prefix: np.ndarray
    delay_sum_prefix: np.ndarray
    max_delay_prefix: np.ndarray

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> "SliceIndex":
        ordered = frame.sort_values("timestamp_epoch", kind="mergesort")
        timestamps = ordered["timestamp_epoch"].to_numpy(dtype=np.int64)
        delays = ordered["atraso_min"].to_numpy(dtype=np.int32)
        delayed_flags = (delays > 30).astype(np.int32)
        delayed_30_prefix = np.concatenate(([0], delayed_flags.cumsum(dtype=np.int64)))
        delay_sum_prefix = np.concatenate(([0], delays.cumsum(dtype=np.int64)))
        max_delay_prefix = np.maximum.accumulate(delays)
        return cls(
            timestamps=timestamps,
            delays=delays,
            delayed_30_prefix=delayed_30_prefix,
            delay_sum_prefix=delay_sum_prefix,
            max_delay_prefix=max_delay_prefix,
        )

    def window_bounds(self, start_ts: int, end_ts: int) -> tuple[int, int]:
        left = int(np.searchsorted(self.timestamps, start_ts, side="left"))
        right = int(np.searchsorted(self.timestamps, end_ts, side="right"))
        return left, right


class IndexedLogRepository(QueryRepository):
    def __init__(self, frame: pd.DataFrame) -> None:
        ordered = frame.sort_values("timestamp_epoch", kind="mergesort").reset_index(drop=True)
        self._frame = ordered
        self._global = SliceIndex.from_frame(ordered)
        self._hub_indexes = self._build_group_indexes(ordered, "hub")
        self._status_indexes = self._build_group_indexes(ordered, "status")
        self._hub_status_indexes = self._build_pair_indexes(ordered)

    def count_delays(self, query: TimeRangeQuery) -> int:
        index = self._resolve_index(query.hub, query.status)
        left, right = index.window_bounds(query.start_ts, query.end_ts)
        if left >= right:
            return 0
        if query.min_delay == 30:
            return int(index.delayed_30_prefix[right] - index.delayed_30_prefix[left])
        delays = index.delays[left:right]
        return int((delays > query.min_delay).sum())

    def summarize_window(self, query: TimeRangeQuery) -> dict[str, float | int]:
        index = self._resolve_index(query.hub, query.status)
        left, right = index.window_bounds(query.start_ts, query.end_ts)
        total_events = right - left
        if total_events <= 0:
            return {
                "total_events": 0,
                "delayed_events": 0,
                "average_delay": 0.0,
                "max_delay": 0,
            }

        delay_sum = int(index.delay_sum_prefix[right] - index.delay_sum_prefix[left])
        max_delay = int(index.delays[left:right].max(initial=0))
        return {
            "total_events": int(total_events),
            "delayed_events": int(self.count_delays(query)),
            "average_delay": round(delay_sum / total_events, 2),
            "max_delay": max_delay,
        }

    def events_frame(self) -> pd.DataFrame:
        return self._frame

    def performance_by_hub(self, start_ts: int, end_ts: int, min_delay: int = 30) -> pd.DataFrame:
        records: list[dict[str, float | int | str]] = []
        for hub, index in self._hub_indexes.items():
            left, right = index.window_bounds(start_ts, end_ts)
            total_events = right - left
            if total_events <= 0:
                continue
            query = TimeRangeQuery(start_ts=start_ts, end_ts=end_ts, min_delay=min_delay, hub=hub)
            delayed = self.count_delays(query)
            records.append(
                {
                    "hub": hub,
                    "eventos": total_events,
                    "atrasos": delayed,
                    "percentual_atraso": round(delayed / total_events, 4),
                }
            )
        return pd.DataFrame(records).sort_values("percentual_atraso", ascending=False)

    @staticmethod
    def _build_group_indexes(frame: pd.DataFrame, column: str) -> dict[str, SliceIndex]:
        return {key: SliceIndex.from_frame(group) for key, group in frame.groupby(column, sort=False)}

    @staticmethod
    def _build_pair_indexes(frame: pd.DataFrame) -> dict[tuple[str, str], SliceIndex]:
        grouped = frame.groupby(["hub", "status"], sort=False)
        return {tuple(key): SliceIndex.from_frame(group) for key, group in grouped}

    def _resolve_index(self, hub: str | None, status: str | None) -> SliceIndex:
        if hub and status:
            return self._hub_status_indexes.get((hub, status), SliceIndex.from_frame(self._frame.iloc[0:0]))
        if hub:
            return self._hub_indexes.get(hub, SliceIndex.from_frame(self._frame.iloc[0:0]))
        if status:
            return self._status_indexes.get(status, SliceIndex.from_frame(self._frame.iloc[0:0]))
        return self._global


def linear_delay_count(events: Iterable[dict[str, object]], start_ts: int, end_ts: int, min_delay: int) -> int:
    total = 0
    for event in events:
        timestamp = int(event["timestamp_epoch"])
        if start_ts <= timestamp <= end_ts and int(event["atraso_min"]) > min_delay:
            total += 1
    return total

