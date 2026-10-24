"""Export natural Amharic sentences from public Telegram channel previews."""
from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from scraper.pipeline.filter import SentenceFilter
from scraper.pipeline.normalize import clean
from scraper.pipeline.segment import split_sentences

NEWS_RE = re.compile(
    r"(ሰበር\s*ዜና|ዜና|መግለጫ|ሚኒስቴር|መንግስት|ፓርላማ|"
    r"ፕሬዝዳንት|ጠቅላይ\s*ሚኒስትር|ሪፖርት|በዛሬው\s*ዕለት)"
)
PROMO_RE = re.compile(
    r"(subscribe|join|follow|share|channel|ሰብስክራይብ|"
    r"ቻናል|ተቀላቀሉ|ይቀላቀሉ|ሼር|ፎሎው|ማስታወቂያ|"
    r"ምዝገባ|ለመመዝገብ|ያስመዘገባችሁ|እንድትገኙ|"
    r"እናሳስባለን|አዘጋጅተናል|በመተባበራችን\s+ታላቅ\s+ኩራት|"
    r"ያለንን\s+ቁርጠኝነት\s+እንቀጥላለን)",
    re.I,
)
URL_RE = re.compile(r"https?://\S+|t\.me/\S+|@\w+|#\S+", re.I)
PHONE_RE = re.compile(r"(?<!\d)\d{9,}(?!\d)")
BROKEN_TAG_RE = re.compile(r"/\s+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--channels", nargs="+", required=True)
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--target-words", type=int)
    parser.add_argument("--exclude-files", nargs="*", type=Path, default=[])
    parser.add_argument("--min-words", type=int, default=5)
    parser.add_argument("--max-words", type=int, default=50)
    parser.add_argument("--max-pages", type=int, default=600)
    parser.add_argument("--delay", type=float, default=0.5)
    return parser.parse_args()


def fetch_page(session: requests.Session, channel: str, before: int | None) -> str:
    url = f"https://t.me/s/{channel}"
    for attempt in range(4):
        try:
            response = session.get(
                url,
                params={"before": before} if before is not None else None,
                timeout=30,
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def page_posts(html: str) -> tuple[list[str], int | None]:
    soup = BeautifulSoup(html, "html.parser")
    posts: list[str] = []
    ids: list[int] = []
    for message in soup.select(".tgme_widget_message"):
        post_ref = message.get("data-post", "")
        match = re.search(r"/(\d+)$", post_ref)
        if match:
            ids.append(int(match.group(1)))
        text_node = message.select_one(".tgme_widget_message_text")
        if text_node:
            posts.append(text_node.get_text("\n", strip=True))
    return posts, min(ids) if ids else None


def natural_sentences(text: str, sentence_filter: SentenceFilter) -> list[str]:
    text = URL_RE.sub(" ", text)
    output: list[str] = []
    for raw_sentence in split_sentences(text):
        sentence = clean(raw_sentence)
        if (
            NEWS_RE.search(sentence)
            or PROMO_RE.search(sentence)
            or PHONE_RE.search(sentence)
            or BROKEN_TAG_RE.search(sentence)
            or any(
                sentence.count(opening) != sentence.count(closing)
                for opening, closing in (("(", ")"), ("[", "]"), ("{", "}"))
            )
            or sentence.count('"') % 2
        ):
            continue
        accepted, _reason = sentence_filter.passes(sentence)
        if accepted:
            output.append(sentence)
    return output


def main() -> int:
    args = parse_args()
    channels = [channel.lstrip("@") for channel in args.channels]
    sentence_filter = SentenceFilter(
        {
            "min_words": args.min_words,
            "max_words": args.max_words,
            "min_ethiopic_ratio": 0.90,
            "require_terminal_punctuation": True,
            "max_url_email_hashtag_ratio": 0.0,
            "max_latin_words": 0,
            "reject_caption_artifacts": True,
            "reject_repeated_words": True,
            "blocklist": [],
        }
    )
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/138 Safari/537.36"
    )

    collected: list[str] = []
    seen: set[str] = set()
    for path in args.exclude_files:
        if path.exists():
            seen.update(
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
    cursors: dict[str, int | None] = {channel: None for channel in channels}
    exhausted: set[str] = set()
    total_words = 0

    for _page_round in range(args.max_pages):
        if (
            len(collected) >= args.limit
            or (args.target_words is not None and total_words >= args.target_words)
            or len(exhausted) == len(channels)
        ):
            break
        for channel in channels:
            if (
                channel in exhausted
                or len(collected) >= args.limit
                or (args.target_words is not None and total_words >= args.target_words)
            ):
                continue
            html = fetch_page(session, channel, cursors[channel])
            posts, oldest_id = page_posts(html)
            if not posts or oldest_id is None or oldest_id == cursors[channel]:
                exhausted.add(channel)
                continue
            cursors[channel] = oldest_id
            for post in posts:
                for sentence in natural_sentences(post, sentence_filter):
                    if sentence in seen:
                        continue
                    seen.add(sentence)
                    collected.append(sentence)
                    total_words += len(sentence.split())
                    if (
                        len(collected) >= args.limit
                        or (args.target_words is not None and total_words >= args.target_words)
                    ):
                        break
                if (
                    len(collected) >= args.limit
                    or (args.target_words is not None and total_words >= args.target_words)
                ):
                    break
            print(
                f"{channel}: before={oldest_id}, "
                f"sentences={len(collected)}, words={total_words}"
            )
            time.sleep(args.delay)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(f"{sentence}\n" for sentence in collected),
        encoding="utf-8",
    )
    print(
        f"Wrote {len(collected)} sentences ({total_words} words) "
        f"to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
