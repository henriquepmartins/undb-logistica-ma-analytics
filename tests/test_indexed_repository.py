from __future__ import annotations

import pandas as pd

from logisticama.adapters.persistence.indexed_repository import IndexedLogRepository, linear_delay_count
from logisticama.domain.ports import TimeRangeQuery
from logisticama.shared.normalization import normalize_logs_frame


def sample_frame() -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {"id": "1", "timestamp": "2026-02-07T09:00:00-03:00", "status": "triagem", "hub": "Ponta_Areia", "atraso_min": 10},
            {"id": "2", "timestamp": "2026-02-07T10:00:00-03:00", "status": "triagem", "hub": "Raposa", "atraso_min": 55},
            {"id": "3", "timestamp": "2026-02-07T11:00:00-03:00", "status": "roteirizado", "hub": "Raposa", "atraso_min": 75},
            {"id": "4", "timestamp": "2026-02-07T12:00:00-03:00", "status": "entregue", "hub": "Ponta_Areia", "atraso_min": 0},
        ]
    )
    return normalize_logs_frame(frame)


def test_indexed_count_matches_linear() -> None:
    frame = sample_frame()
    repo = IndexedLogRepository(frame)
    start_ts = int(frame["timestamp_epoch"].min())
    end_ts = int(frame["timestamp_epoch"].max())

    linear = linear_delay_count(frame.to_dict("records"), start_ts, end_ts, 30)
    indexed = repo.count_delays(TimeRangeQuery(start_ts=start_ts, end_ts=end_ts, min_delay=30))

    assert linear == indexed == 2


def test_hub_filtered_summary() -> None:
    frame = sample_frame()
    repo = IndexedLogRepository(frame)
    raposa_frame = frame[frame["hub"] == "Raposa"]
    start_ts = int(raposa_frame["timestamp_epoch"].min())
    end_ts = int(raposa_frame["timestamp_epoch"].max())

    summary = repo.summarize_window(TimeRangeQuery(start_ts=start_ts, end_ts=end_ts, min_delay=30, hub="Raposa"))

    assert summary["total_events"] == 2
    assert summary["delayed_events"] == 2
    assert summary["max_delay"] == 75


def test_status_filtered_summary() -> None:
    frame = sample_frame()
    repo = IndexedLogRepository(frame)
    roteirizado_frame = frame[frame["status"] == "roteirizado"]
    start_ts = int(roteirizado_frame["timestamp_epoch"].min())
    end_ts = int(roteirizado_frame["timestamp_epoch"].max())

    summary = repo.summarize_window(
        TimeRangeQuery(start_ts=start_ts, end_ts=end_ts, min_delay=30, status="roteirizado")
    )

    assert summary["total_events"] == 1
    assert summary["delayed_events"] == 1
    assert summary["max_delay"] == 75


def test_min_delay_variation_count() -> None:
    frame = sample_frame()
    repo = IndexedLogRepository(frame)
    start_ts = int(frame["timestamp_epoch"].min())
    end_ts = int(frame["timestamp_epoch"].max())

    count_over_60 = repo.count_delays(TimeRangeQuery(start_ts=start_ts, end_ts=end_ts, min_delay=60))

    assert count_over_60 == 1
