from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class CorpusWriter:
    def __init__(self, jsonl_path: str, db_path: str):
        self.jsonl_path = Path(jsonl_path)
        self.db_path = Path(db_path)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.db_path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS articles (
                url TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                processed_at TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sentence_hashes (
                hash TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            );
            """
        )
        self.db.commit()

    def known_hashes(self) -> set[str]:
        return {row[0] for row in self.db.execute("SELECT hash FROM sentence_hashes")}

    def article_seen(self, url: str) -> bool:
        row = self.db.execute(
            "SELECT 1 FROM articles WHERE url = ? AND status = 'processed'", (url,)
        ).fetchone()
        return row is not None

    def append(self, sentence: str, sentence_hash: str, metadata: dict) -> None:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        record = {
            "sentence": sentence,
            **metadata,
            "word_count": len(sentence.split()),
            "char_count": len(sentence),
            "scraped_at": now,
        }
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
        self.db.execute(
            "INSERT OR IGNORE INTO sentence_hashes(hash, created_at) VALUES (?, ?)",
            (sentence_hash, now),
        )
        self.db.commit()

    def mark_article(self, url: str, source: str, status: str = "processed") -> None:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.db.execute(
            """
            INSERT INTO articles(url, source, processed_at, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                source=excluded.source,
                processed_at=excluded.processed_at,
                status=excluded.status
            """,
            (url, source, now, status),
        )
        self.db.commit()

    def sample(self, count: int) -> list[dict]:
        if not self.jsonl_path.exists():
            return []
        import random

        with self.jsonl_path.open(encoding="utf-8") as handle:
            records = [json.loads(line) for line in handle if line.strip()]
        return random.sample(records, min(count, len(records)))

    def close(self) -> None:
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


