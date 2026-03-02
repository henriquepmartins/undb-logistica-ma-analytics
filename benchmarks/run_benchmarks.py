from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from logisticama.adapters.persistence.indexed_repository import IndexedLogRepository, linear_delay_count
from logisticama.domain.ports import TimeRangeQuery
from logisticama.shared.normalization import normalize_logs_frame


HUBS = ["Ponta_Areia", "Raposa", "Paco_do_Lumiar", "Alcantara", "Centro", "Cohama", "Maiobao", "Anjo_da_Guarda"]
STATUSES = ["coleta", "triagem", "roteirizado", "saiu_para_entrega", "entregue", "atrasado"]


def generate_frame(size: int) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    timestamps = pd.date_range("2026-02-01", periods=size, freq="s", tz="America/Fortaleza")
    frame = pd.DataFrame(
        {
            "id": [f"LM20260201-{i:07d}" for i in range(size)],
            "timestamp": timestamps.astype(str),
            "status": rng.choice(STATUSES, size=size),
            "hub": rng.choice(HUBS, size=size),
            "atraso_min": rng.integers(0, 90, size=size),
        }
    )
    return normalize_logs_frame(frame)


def benchmark(size: int) -> dict[str, float | int]:
    frame = generate_frame(size)
    repository = IndexedLogRepository(frame)
    records = frame.to_dict("records")
    start_ts = int(frame["timestamp_epoch"].iloc[size // 4])
    end_ts = int(frame["timestamp_epoch"].iloc[min(size - 1, size // 4 + size // 2)])

    linear_start = time.perf_counter()
    linear_result = linear_delay_count(records, start_ts, end_ts, 30)
    linear_time = time.perf_counter() - linear_start

    indexed_start = time.perf_counter()
    indexed_result = repository.count_delays(TimeRangeQuery(start_ts=start_ts, end_ts=end_ts, min_delay=30))
    indexed_time = time.perf_counter() - indexed_start

    return {
        "n": size,
        "linear_seconds": round(linear_time, 6),
        "indexed_seconds": round(indexed_time, 6),
        "speedup_x": round(linear_time / max(indexed_time, 1e-9), 2),
        "same_answer": linear_result == indexed_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmarks do motor LogisticaMA.")
    parser.add_argument("--sizes", nargs="+", type=int, default=[1_000, 10_000, 100_000])
    args = parser.parse_args()

    results = [benchmark(size) for size in args.sizes]
    print(pd.DataFrame(results).to_string(index=False))


if __name__ == "__main__":
    main()
