from __future__ import annotations

import csv
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import TextIO

from .types import Sample
from ..constants import CSV_COLUMNS


class SessionDataStore:
    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir
        self._file: TextIO | None = None
        self._writer: csv.DictWriter | None = None
        self._path: Path | None = None

    @property
    def current_path(self) -> Path | None:
        return self._path

    def start_session(self, device_label: str) -> Path:
        self.stop_session()
        sessions_dir = self._root_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_label = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in device_label)[:80]
        self._path = sessions_dir / f"{safe_label}_{ts}.csv"

        self._file = self._path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=CSV_COLUMNS)
        self._writer.writeheader()
        self._file.flush()
        return self._path

    def append(self, sample: Sample) -> None:
        if not self._writer or not self._file:
            return
        self._writer.writerow(asdict(sample))
        self._file.flush()

    def stop_session(self) -> None:
        if self._file:
            try:
                self._file.close()
            finally:
                self._file = None
                self._writer = None
                self._path = None

