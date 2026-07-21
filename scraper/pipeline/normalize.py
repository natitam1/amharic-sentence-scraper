import re
import unicodedata

LEADING_RE = re.compile(r"^(?:[\s•●▪◦*#]+|\(?\d+[.)፡]\s*)+")
QUOTES = "\"'“”‘’«»‹›"


def clean(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = LEADING_RE.sub("", text.strip())
    text = text.strip(QUOTES + " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([።፡፣፤፥፦!?])", r"\1", text)
    text = re.sub(r"([።!?])\1+", r"\1", text)
    return text.strip()


def fingerprint_text(text: str) -> str:
    text = clean(text).casefold()
    return re.sub(r"[^\w\u1200-\u137f]+", "", text)

