from __future__ import annotations

import io
import json
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from logisticama.shared.normalization import REQUIRED_COLUMNS, normalize_logs_frame


class FileLogSource:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> pd.DataFrame:
        return _read_any_source(self.path, self.path.suffix.lower())


class UploadedLogSource:
    def __init__(self, uploaded_file: BinaryIO, file_name: str) -> None:
        self.uploaded_file = uploaded_file
        self.file_name = file_name

    def load(self) -> pd.DataFrame:
        suffix = Path(self.file_name).suffix.lower()
        payload = self.uploaded_file.read()
        buffer = io.BytesIO(payload)
        return _read_any_source(buffer, suffix)


def _read_any_source(source: str | Path | io.BytesIO, suffix: str) -> pd.DataFrame:
    if suffix == ".csv":
        frame = pd.read_csv(source)
        return normalize_logs_frame(frame)

    if suffix == ".json":
        return _read_json(source)

    raise ValueError("Formato nao suportado. Use arquivos CSV ou JSON.")


def _read_json(source: str | Path | io.BytesIO) -> pd.DataFrame:
    frame: pd.DataFrame | None = None
    try:
        candidate = pd.read_json(source, lines=True)
        if all(column in candidate.columns for column in REQUIRED_COLUMNS):
            frame = candidate
    except ValueError:
        frame = None

    if frame is None:
        if isinstance(source, io.BytesIO):
            source.seek(0)
            payload = source.read().decode("utf-8")
        else:
            payload = Path(source).read_text(encoding="utf-8")
        parsed = json.loads(payload)
        frame = pd.DataFrame(parsed)

    return normalize_logs_frame(frame)
