"""本地调用台账：orders.jsonl，每行一次 API 调用摘要（无密钥）。"""

from __future__ import annotations

import json
from pathlib import Path

from .client import CallRecord
from .config import Config

DEFAULT_LEDGER_NAME = "orders.jsonl"


def ledger_path(config: Config) -> Path:
    return config.ledger_path or Path(__file__).resolve().parent.parent / DEFAULT_LEDGER_NAME


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: CallRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record.__dict__, ensure_ascii=False, default=str)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def tail(self, limit: int = 20) -> list[dict]:
        if not self.path.is_file():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        records = []
        for line in lines[-limit:]:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records
