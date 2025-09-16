from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path
class CsvLogger:
    def __init__(self, dir_path: Path, base_name: str = "session"):
        self.dir = dir_path; self.dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file = self.dir / f"{base_name}_{ts}.csv"
        self._fh = open(self.file, "w", newline="", encoding="utf-8")
        self._wr = csv.writer(self._fh); self._wr.writerow(["timestamp", "topic", "value"])
    def log(self, topic: str, value: str):
        ts = datetime.now().isoformat(timespec="seconds")
        self._wr.writerow([ts, topic, value]); self._fh.flush()
    def close(self):
        try: self._fh.close()
        except Exception: pass
