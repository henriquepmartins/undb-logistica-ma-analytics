from __future__ import annotations

import io
import importlib.util
import json
from pathlib import Path

import pandas as pd

from logisticama.adapters.ingest.loaders import FileLogSource, UploadedLogSource
from logisticama.adapters.persistence.indexed_repository import IndexedLogRepository, linear_delay_count
from logisticama.application.benchmarking import (
    DEFAULT_BENCHMARK_SIZES,
    benchmark_cases,
    benchmark_real_case,
    generate_benchmark_frame,
    load_benchmark_profile,
)
from logisticama.application.datasets import OFFICIAL_DATASET_PATH, load_official_frame
from logisticama.application.dto import QueryWindow
from logisticama.application.use_cases import QueryLogisticsDashboard
from logisticama.domain.ports import TimeRangeQuery
from logisticama.shared.normalization import REQUIRED_COLUMNS


NORMALIZED_COLUMNS = set(REQUIRED_COLUMNS) | {
    "timestamp_epoch",
    "timestamp_label",
    "data",
    "hora",
    "esta_atrasado_30",
}

BENCHMARK_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "benchmarks" / "run_benchmarks.py"
STREAMLIT_APP_PATH = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


def sample_records() -> list[dict[str, object]]:
    return [
        {
            "id": "1",
            "timestamp": "2026-02-07T09:00:00-03:00",
            "status": "triagem",
            "hub": "Ponta_Areia",
            "atraso_min": 10,
        },
        {
            "id": "2",
            "timestamp": "2026-02-07T10:30:00-03:00",
            "status": "atrasado",
            "hub": "Raposa",
            "atraso_min": 55,
        },
    ]


def canonical_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    canonical = frame.copy()
    canonical["timestamp"] = canonical["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return canonical[REQUIRED_COLUMNS].to_dict("records")


def load_benchmark_cli_module():
    spec = importlib.util.spec_from_file_location("logisticama_benchmark_cli", BENCHMARK_SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_official_dataset_loads_without_upload() -> None:
    assert OFFICIAL_DATASET_PATH.exists()

    frame = load_official_frame()

    assert not frame.empty
    assert NORMALIZED_COLUMNS.issubset(frame.columns)


def test_timestamp_epoch_matches_timezone_aware_timestamp_seconds() -> None:
    frame = load_official_frame().head(25)
    expected = frame["timestamp"].map(lambda value: int(value.timestamp()))

    assert frame["timestamp_epoch"].tolist() == expected.tolist()


def test_csv_and_json_ingestion_share_the_same_contract(tmp_path) -> None:
    records = sample_records()
    csv_path = tmp_path / "logs.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)

    csv_frame = FileLogSource(csv_path).load()
    json_payload = io.BytesIO(json.dumps(records).encode("utf-8"))
    json_frame = UploadedLogSource(json_payload, "logs.json").load()

    assert NORMALIZED_COLUMNS.issubset(csv_frame.columns)
    assert NORMALIZED_COLUMNS.issubset(json_frame.columns)
    assert canonical_records(csv_frame) == canonical_records(json_frame)


def test_benchmark_parser_defaults_cover_the_assignment_sizes() -> None:
    module = load_benchmark_cli_module()
    args = module.build_parser().parse_args([])

    assert tuple(args.sizes) == DEFAULT_BENCHMARK_SIZES


def test_generated_benchmark_frame_uses_categories_from_official_dataset() -> None:
    official = load_official_frame()
    profile = load_benchmark_profile()
    frame = generate_benchmark_frame(500, profile=profile)

    assert set(frame["status"].unique()).issubset(set(official["status"].unique()))
    assert set(frame["hub"].unique()).issubset(set(official["hub"].unique()))


def test_real_dataset_indexed_matches_linear_for_a_time_window() -> None:
    frame = load_official_frame()
    repository = IndexedLogRepository(frame)
    records = frame.to_dict("records")
    start_ts = int(frame["timestamp_epoch"].quantile(0.2))
    end_ts = int(frame["timestamp_epoch"].quantile(0.8))

    linear = linear_delay_count(records, start_ts, end_ts, 30)
    indexed = repository.count_delays(TimeRangeQuery(start_ts=start_ts, end_ts=end_ts, min_delay=30))

    assert linear == indexed


def test_real_dataset_indexed_matches_manual_filtered_query() -> None:
    frame = load_official_frame()
    repository = IndexedLogRepository(frame)
    records = frame.to_dict("records")
    hub = str(frame["hub"].mode().iat[0])
    status = str(frame["status"].mode().iat[0])
    start_ts = int(frame["timestamp_epoch"].quantile(0.1))
    end_ts = int(frame["timestamp_epoch"].quantile(0.9))
    min_delay = 45

    expected = sum(
        1
        for event in records
        if start_ts <= int(event["timestamp_epoch"]) <= end_ts
        and event["hub"] == hub
        and event["status"] == status
        and int(event["atraso_min"]) > min_delay
    )
    indexed = repository.count_delays(
        TimeRangeQuery(start_ts=start_ts, end_ts=end_ts, min_delay=min_delay, hub=hub, status=status)
    )

    assert indexed == expected


def test_operational_summary_matches_manual_global_window() -> None:
    frame = load_official_frame()
    service = QueryLogisticsDashboard(IndexedLogRepository(frame))
    start = frame["timestamp_label"].min().floor("min")
    end = frame["timestamp_label"].max().ceil("min")
    window = QueryWindow(start_iso=start.isoformat(), end_iso=end.isoformat(), min_delay=30)

    summary = service.build_summary(window)
    manual_mask = (frame["timestamp_label"] >= start) & (frame["timestamp_label"] <= end)
    manual_frame = frame.loc[manual_mask]

    assert summary.total_events == int(manual_mask.sum())
    assert summary.delayed_events == int((manual_frame["atraso_min"] > 30).sum())
    assert summary.average_delay == round(float(manual_frame["atraso_min"].mean()), 2)
    assert summary.max_delay == int(manual_frame["atraso_min"].max())


def test_real_case_benchmark_matches_manual_count() -> None:
    frame = load_official_frame()
    result = benchmark_real_case(frame)
    ordered = frame.sort_values("timestamp_epoch", kind="mergesort").reset_index(drop=True)
    start_index = len(ordered) // 4
    end_index = min(len(ordered) - 1, start_index + len(ordered) // 2)
    start_ts = int(ordered["timestamp_epoch"].iloc[start_index])
    end_ts = int(ordered["timestamp_epoch"].iloc[end_index])
    manual_mask = (ordered["timestamp_epoch"] >= start_ts) & (ordered["timestamp_epoch"] <= end_ts)
    manual_delayed = int((manual_mask & (ordered["atraso_min"] > result.min_delay)).sum())

    assert result.same_answer is True
    assert result.total_events == int(manual_mask.sum())
    assert result.delayed_events == manual_delayed
    assert result.linear_runs > 0
    assert result.indexed_runs > 0
    assert result.linear_query_seconds > 0
    assert result.indexed_query_seconds > 0


def test_benchmark_frame_exposes_runtime_metadata() -> None:
    frame = benchmark_cases((1_000, 10_000))

    assert {"linear_runs", "indexed_runs"}.issubset(frame.columns)
    assert (frame["linear_runs"] > 0).all()
    assert (frame["indexed_runs"] > 0).all()
    assert (frame["linear_query_seconds"] > 0).all()
    assert (frame["indexed_query_seconds"] > 0).all()


def test_streamlit_app_uses_hardcoded_base_and_has_no_uploader() -> None:
    contents = STREAMLIT_APP_PATH.read_text(encoding="utf-8")

    assert "file_uploader" not in contents
    assert "st.sidebar" not in contents
    assert "st.tabs(" in contents
    assert "load_official_frame" in contents
    assert "PAGE_OPERATION" in contents
    assert "PAGE_BENCHMARK" in contents
    assert "μs" in contents
    assert "Resumo do algoritmo novo" in contents
