from __future__ import annotations

import re
import unicodedata

TERMINAL_RE = re.compile(r"(?:፡፡|[።!?])$")
LINK_TOKEN_RE = re.compile(r"(?:https?://|www\.|\S+@\S+|#\S+)", re.I)


class SentenceFilter:
    def __init__(self, config: dict):
        self.min_words = int(config["min_words"])
        self.max_words = int(config["max_words"])
        self.min_ethiopic_ratio = float(config["min_ethiopic_ratio"])
        self.require_terminal = bool(config.get("require_terminal_punctuation", True))
        self.max_link_ratio = float(config.get("max_url_email_hashtag_ratio", 0.2))
        self.blocklist = [value.casefold() for value in config.get("blocklist", [])]

    def passes(self, sentence: str) -> tuple[bool, str]:
        words = sentence.split()
        if not self.min_words <= len(words) <= self.max_words:
            return False, "length"
        if self.require_terminal and not TERMINAL_RE.search(sentence):
            return False, "terminal"
        if any(pattern in sentence.casefold() for pattern in self.blocklist):
            return False, "boilerplate"
        if self._ethiopic_ratio(sentence) < self.min_ethiopic_ratio:
            return False, "script"
        if len(LINK_TOKEN_RE.findall(sentence)) / max(len(words), 1) > self.max_link_ratio:
            return False, "links"
        first = next((char for char in sentence if not char.isspace()), "")
        if not first or unicodedata.category(first)[0] not in {"L", "N", "P"}:
            return False, "opening"
        return True, "ok"

    @staticmethod
    def _ethiopic_ratio(text: str) -> float:
        letters = [char for char in text if char.isalpha()]
        if not letters:
            return 0.0
        ethiopic = sum("\u1200" <= char <= "\u137f" for char in letters)
        return ethiopic / len(letters)

