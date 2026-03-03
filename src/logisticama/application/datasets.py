from __future__ import annotations

from pathlib import Path

import pandas as pd

from logisticama.adapters.ingest.loaders import FileLogSource


OFFICIAL_DATASET_PATH = Path("data/logistica_ma_logs.csv")


def load_official_frame(path: str | Path = OFFICIAL_DATASET_PATH) -> pd.DataFrame:
    return FileLogSource(Path(path)).load()
