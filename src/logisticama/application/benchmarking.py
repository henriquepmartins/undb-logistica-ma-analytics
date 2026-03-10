from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

from logisticama.adapters.persistence.indexed_repository import IndexedLogRepository, linear_delay_count
from logisticama.application.datasets import load_official_frame
from logisticama.domain.ports import TimeRangeQuery
from logisticama.shared.normalization import normalize_logs_frame


DEFAULT_BENCHMARK_SIZES = (1_000, 10_000, 100_000, 1_000_000, 2_000_000)
LINEAR_BENCHMARK_RUNS = 5
INDEXED_BENCHMARK_RUNS = 200


@dataclass(frozen=True, slots=True)
class BenchmarkProfile:
    start_timestamp: pd.Timestamp
    statuses: tuple[str, ...]
    hubs: tuple[str, ...]
    delay_values: np.ndarray


@dataclass(frozen=True, slots=True)
class RealCaseBenchmark:
    start_label: str
    end_label: str
    min_delay: int
    total_events: int
    delayed_events: int
    build_seconds: float
    linear_query_seconds: float
    indexed_query_seconds: float
    linear_runs: int
    indexed_runs: int
    speedup_x: float
    same_answer: bool


def load_benchmark_profile() -> BenchmarkProfile:
    frame = load_official_frame()
    start_timestamp = frame["timestamp_label"].min().floor("s")
    statuses = tuple(frame["status"].dropna().astype(str).unique().tolist())
    hubs = tuple(frame["hub"].dropna().astype(str).unique().tolist())
    delay_values = frame["atraso_min"].to_numpy(dtype=np.int32)
    return BenchmarkProfile(
        start_timestamp=start_timestamp,
        statuses=statuses,
        hubs=hubs,
        delay_values=delay_values,
    )


def generate_benchmark_frame(size: int, profile: BenchmarkProfile | None = None) -> pd.DataFrame:
    benchmark_profile = profile or load_benchmark_profile()
    rng = np.random.default_rng(42)
    timestamps = pd.date_range(benchmark_profile.start_timestamp, periods=size, freq="s")
    frame = pd.DataFrame(
        {
            "id": [f"LM20260201-{i:07d}" for i in range(size)],
            "timestamp": timestamps.astype(str),
            "status": rng.choice(benchmark_profile.statuses, size=size),
            "hub": rng.choice(benchmark_profile.hubs, size=size),
            "atraso_min": rng.choice(benchmark_profile.delay_values, size=size),
        }
    )
    return normalize_logs_frame(frame)


def average_query_seconds(callback, runs: int) -> float:
    start = time.perf_counter()
    for _ in range(runs):
        callback()
    return (time.perf_counter() - start) / runs


def benchmark_case(size: int, profile: BenchmarkProfile | None = None) -> dict[str, float | int | bool]:
    frame = generate_benchmark_frame(size, profile=profile)

    build_start = time.perf_counter()
    repository = IndexedLogRepository(frame)
    build_seconds = time.perf_counter() - build_start

    records = frame.to_dict("records")
    start_ts = int(frame["timestamp_epoch"].iloc[size // 4])
    end_ts = int(frame["timestamp_epoch"].iloc[min(size - 1, size // 4 + size // 2)])
    query = TimeRangeQuery(start_ts=start_ts, end_ts=end_ts, min_delay=30)

    linear_result = linear_delay_count(records, start_ts, end_ts, 30)
    indexed_result = repository.count_delays(query)
    linear_query_seconds = average_query_seconds(
        lambda: linear_delay_count(records, start_ts, end_ts, 30),
        LINEAR_BENCHMARK_RUNS,
    )
    indexed_query_seconds = average_query_seconds(
        lambda: repository.count_delays(query),
        INDEXED_BENCHMARK_RUNS,
    )

    return {
        "n": size,
        "build_seconds": build_seconds,
        "linear_query_seconds": linear_query_seconds,
        "indexed_query_seconds": indexed_query_seconds,
        "linear_runs": LINEAR_BENCHMARK_RUNS,
        "indexed_runs": INDEXED_BENCHMARK_RUNS,
        "speedup_x": round(linear_query_seconds / max(indexed_query_seconds, 1e-9), 2),
        "same_answer": linear_result == indexed_result,
    }


def benchmark_cases(
    sizes: tuple[int, ...] = DEFAULT_BENCHMARK_SIZES,
    profile: BenchmarkProfile | None = None,
) -> pd.DataFrame:
    benchmark_profile = profile or load_benchmark_profile()
    return pd.DataFrame([benchmark_case(size, profile=benchmark_profile) for size in sizes])


def benchmark_real_case(frame: pd.DataFrame | None = None, min_delay: int = 30) -> RealCaseBenchmark:
    official_frame = frame if frame is not None else load_official_frame()
    ordered = official_frame.sort_values("timestamp_epoch", kind="mergesort").reset_index(drop=True)
    total_rows = len(ordered)
    start_index = total_rows // 4
    end_index = min(total_rows - 1, start_index + total_rows // 2)
    start_ts = int(ordered["timestamp_epoch"].iloc[start_index])
    end_ts = int(ordered["timestamp_epoch"].iloc[end_index])
    query = TimeRangeQuery(start_ts=start_ts, end_ts=end_ts, min_delay=min_delay)

    build_start = time.perf_counter()
    repository = IndexedLogRepository(ordered)
    build_seconds = time.perf_counter() - build_start

    records = ordered.to_dict("records")
    delayed_events = linear_delay_count(records, start_ts, end_ts, min_delay)
    indexed_events = repository.count_delays(query)
    linear_query_seconds = average_query_seconds(
        lambda: linear_delay_count(records, start_ts, end_ts, min_delay),
        LINEAR_BENCHMARK_RUNS,
    )
    indexed_query_seconds = average_query_seconds(
        lambda: repository.count_delays(query),
        INDEXED_BENCHMARK_RUNS,
    )

    window_mask = (ordered["timestamp_epoch"] >= start_ts) & (ordered["timestamp_epoch"] <= end_ts)
    start_label = ordered["timestamp_label"].iloc[start_index].strftime("%d/%m/%Y %H:%M")
    end_label = ordered["timestamp_label"].iloc[end_index].strftime("%d/%m/%Y %H:%M")

    return RealCaseBenchmark(
        start_label=start_label,
        end_label=end_label,
        min_delay=min_delay,
        total_events=int(window_mask.sum()),
        delayed_events=int(delayed_events),
        build_seconds=build_seconds,
        linear_query_seconds=linear_query_seconds,
        indexed_query_seconds=indexed_query_seconds,
        linear_runs=LINEAR_BENCHMARK_RUNS,
        indexed_runs=INDEXED_BENCHMARK_RUNS,
        speedup_x=round(linear_query_seconds / max(indexed_query_seconds, 1e-9), 2),
        same_answer=delayed_events == indexed_events,
    )
