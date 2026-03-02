from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = ["id", "timestamp", "status", "hub", "atraso_min"]


def normalize_logs_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"O dataset nao possui as colunas obrigatorias: {', '.join(missing)}")

    normalized = frame[REQUIRED_COLUMNS].copy()
    normalized["id"] = normalized["id"].astype(str)
    normalized["status"] = normalized["status"].fillna("desconhecido").astype(str)
    normalized["hub"] = normalized["hub"].fillna("desconhecido").astype(str)
    normalized["atraso_min"] = pd.to_numeric(normalized["atraso_min"], errors="coerce").fillna(0).astype(int)
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="coerce", utc=True)
    normalized = normalized.dropna(subset=["timestamp"]).reset_index(drop=True)
    normalized["timestamp_epoch"] = (normalized["timestamp"].astype("int64") // 1_000_000_000).astype("int64")
    normalized["timestamp_label"] = normalized["timestamp"].dt.tz_convert("America/Fortaleza")
    normalized["data"] = normalized["timestamp_label"].dt.date.astype(str)
    normalized["hora"] = normalized["timestamp_label"].dt.hour
    normalized["esta_atrasado_30"] = normalized["atraso_min"] > 30
    return normalized
