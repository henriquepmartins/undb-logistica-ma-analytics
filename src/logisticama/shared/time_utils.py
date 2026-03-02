from __future__ import annotations

import pandas as pd


def parse_iso_to_epoch_seconds(value: str) -> int:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("America/Fortaleza")
    return int(stamp.tz_convert("UTC").timestamp())


def ensure_fortaleza_timestamp(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        return stamp.tz_localize("America/Fortaleza")
    return stamp.tz_convert("America/Fortaleza")
