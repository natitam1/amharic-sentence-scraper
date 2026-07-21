import re

BOUNDARY_RE = re.compile(r".+?(?:፡፡|[።!?])(?=\s|$)", re.DOTALL)
SPACE_RE = re.compile(r"[ \t\r\f\v]+")


def split_sentences(text: str) -> list[str]:
    text = SPACE_RE.sub(" ", text.replace("\u00a0", " "))
    text = re.sub(r"\n+", "\n", text)
    sentences: list[str] = []
    for block in text.splitlines():
        block = block.strip()
        if not block:
            continue
        sentences.extend(match.group(0).strip() for match in BOUNDARY_RE.finditer(block))
    return sentences

