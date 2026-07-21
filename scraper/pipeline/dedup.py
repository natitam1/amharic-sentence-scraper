from __future__ import annotations

import hashlib
from collections import defaultdict, deque

from scraper.pipeline.normalize import fingerprint_text


class Deduplicator:
    def __init__(self, config: dict, known_hashes: set[str] | None = None):
        self.threshold = float(config["similarity_threshold"])
        self.window_size = int(config["rolling_window"])
        self.bucket_size = int(config["length_bucket_size"])
        self.prefix_chars = int(config["prefix_chars"])
        self.hashes = set(known_hashes or ())
        self.buckets: dict[tuple[int, str], deque[set[str]]] = defaultdict(
            lambda: deque(maxlen=self.window_size)
        )

    @staticmethod
    def digest(text: str) -> str:
        return hashlib.sha256(fingerprint_text(text).encode("utf-8")).hexdigest()

    def is_duplicate(self, text: str) -> tuple[bool, str]:
        normalized = fingerprint_text(text)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if digest in self.hashes:
            return True, digest

        grams = self._ngrams(normalized)
        length_bucket = len(normalized) // self.bucket_size
        prefix = normalized[: self.prefix_chars]
        candidates = []
        for bucket in (length_bucket - 1, length_bucket, length_bucket + 1):
            candidates.extend(self.buckets.get((bucket, prefix), ()))
        if any(self._jaccard(grams, candidate) >= self.threshold for candidate in candidates):
            return True, digest

        self.hashes.add(digest)
        self.buckets[(length_bucket, prefix)].append(grams)
        return False, digest

    @staticmethod
    def _ngrams(text: str, size: int = 3) -> set[str]:
        return {text[i : i + size] for i in range(max(1, len(text) - size + 1))}

    @staticmethod
    def _jaccard(left: set[str], right: set[str]) -> float:
        union = left | right
        return len(left & right) / len(union) if union else 1.0

