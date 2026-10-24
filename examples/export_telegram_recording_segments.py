"""Export natural Amharic Telegram text as 15-30 second recording segments."""
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
    r"(ሰበር\s*ዜና|ዜና|መግለጫ|ጋዜጣዊ|ሚኒስቴር|መንግስት|"
    r"ፓርላማ|ፕሬዝዳንት|ጠቅላይ\s*ሚኒስትር|የምርጫ\s*ቦርድ|"
    r"እንደዘገበው|በሰጡት\s*መግለጫ|የዜና\s*ዘገባ)"
)
PROMO_RE = re.compile(
    r"(subscribe|join|follow|share|channel|ሰብስክራይብ|ቻናል|"
    r"ተቀላቀሉ|ይቀላቀሉ|ሼር|ፎሎው|ማስታወቂያ)",
    re.I,
)
URL_RE = re.compile(r"https?://\S+|t\.me/\S+|@\w+|#\S+", re.I)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--channels", nargs="+", required=True)
    parser.add_argument("--limit", type=int, default=15000)
    parser.add_argument("--min-words", type=int, default=30)
    parser.add_argument("--max-words", type=int, default=60)
    parser.add_argument("--max-pages", type=int, default=1500)
    parser.add_argument("--delay", type=float, default=0.5)
    return parser.parse_args()


def fetch_page(session: requests.Session, channel: str, before: int | None) -> str:
    url = f"https://t.me/s/{channel}"
    last_error: requests.RequestException | None = None
    for attempt in range(6):
        try:
            response = session.get(
                url,
                params={"before": before} if before is not None else None,
                timeout=30,
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 5:
                time.sleep(2**attempt)
    assert last_error is not None
    raise last_error


def page_posts(html: str) -> tuple[list[str], int | None]:
    soup = BeautifulSoup(html, "html.parser")
    posts: list[str] = []
    ids: list[int] = []
    for message in soup.select(".tgme_widget_message"):
        match = re.search(r"/(\d+)$", message.get("data-post", ""))
        if match:
            ids.append(int(match.group(1)))
        text_node = message.select_one(".tgme_widget_message_text")
        if text_node:
            posts.append(text_node.get_text("\n", strip=True))
    return posts, min(ids) if ids else None


def post_sentences(text: str, sentence_filter: SentenceFilter) -> list[str]:
    text = URL_RE.sub(" ", text)
    output: list[str] = []
    for raw_sentence in split_sentences(text):
        sentence = clean(raw_sentence)
        if NEWS_RE.search(sentence) or PROMO_RE.search(sentence):
            continue
        accepted, _reason = sentence_filter.passes(sentence)
        if accepted:
            output.append(sentence)
    return output


def recording_segments(
    sentences: list[str], min_words: int, max_words: int
) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    current_words = 0
    for sentence in sentences:
        count = len(sentence.split())
        if count > max_words:
            continue
        if current and current_words + count > max_words:
            if current_words >= min_words:
                segments.append(" ".join(current))
            current = []
            current_words = 0
        current.append(sentence)
        current_words += count
        if current_words >= min_words:
            segments.append(" ".join(current))
            current = []
            current_words = 0
    return segments


def main() -> int:
    args = parse_args()
    channels = [channel.lstrip("@") for channel in args.channels]
    sentence_filter = SentenceFilter(
        {
            "min_words": 3,
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
    cursors: dict[str, int | None] = {channel: None for channel in channels}
    exhausted: set[str] = set()
    for _page_round in range(args.max_pages):
        if len(collected) >= args.limit or len(exhausted) == len(channels):
            break
        for channel in channels:
            if channel in exhausted or len(collected) >= args.limit:
                continue
            html = fetch_page(session, channel, cursors[channel])
            posts, oldest_id = page_posts(html)
            if not posts or oldest_id is None or oldest_id == cursors[channel]:
                exhausted.add(channel)
                continue
            cursors[channel] = oldest_id
            for post in posts:
                sentences = post_sentences(post, sentence_filter)
                for segment in recording_segments(
                    sentences, args.min_words, args.max_words
                ):
                    if segment in seen:
                        continue
                    seen.add(segment)
                    collected.append(segment)
                    if len(collected) >= args.limit:
                        break
                if len(collected) >= args.limit:
                    break
            print(f"{channel}: before={oldest_id}, total={len(collected)}")
            time.sleep(args.delay)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(f"{segment}\n" for segment in collected),
        encoding="utf-8",
    )
    print(
        f"Wrote {len(collected)} recording segments to {args.output} "
        f"({args.min_words}-{args.max_words} words each)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
