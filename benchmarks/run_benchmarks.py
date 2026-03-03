from __future__ import annotations

import argparse
import pandas as pd

from logisticama.application.benchmarking import DEFAULT_BENCHMARK_SIZES, benchmark_cases


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmarks do motor LogisticaMA.")
    parser.add_argument("--sizes", nargs="+", type=int, default=list(DEFAULT_BENCHMARK_SIZES))
    return parser


def _assert_sla(results: pd.DataFrame, sla_seconds: float = 3.0, target_size: int = 2_000_000) -> None:
    if "n" not in results.columns or "indexed_query_seconds" not in results.columns:
        return
    if target_size not in results["n"].values:
        return
    row = results.loc[results["n"] == target_size].iloc[0]
    indexed_seconds = float(row["indexed_query_seconds"])
    if indexed_seconds >= sla_seconds:
        raise AssertionError(
            f"SLA de {sla_seconds}s não atingido para n={target_size}: indexado={indexed_seconds:.4f}s"
        )
    if "same_answer" in results.columns and not bool(row["same_answer"]):
        raise AssertionError("Resultado indexado diverge do baseline no maior cenário")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    results = benchmark_cases(tuple(args.sizes))
    _assert_sla(results)
    print(pd.DataFrame(results).to_string(index=False))


if __name__ == "__main__":
    main()
