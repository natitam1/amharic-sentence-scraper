"""Export natural Amharic sentences from public personal blogs."""
from __future__ import annotations

import argparse
import html
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

from scraper.pipeline.filter import SentenceFilter
from scraper.pipeline.normalize import clean
from scraper.pipeline.segment import split_sentences

BLOGGER_SOURCES = (
    ("mezemirethiopia", "https://mezemirethiopia.blogspot.com/feeds/posts/default"),
    ("zone9ethio", "https://zone9ethio.blogspot.com/feeds/posts/default"),
)
WORDPRESS_SOURCES = (
    ("lozadmasu", "https://lozadmasu.wordpress.com/wp-json/wp/v2/posts"),
)
NEWS_RE = re.compile(
    r"(ሰበር\s*ዜና|ዜና|የዜና\s*ዘገባ|መግለጫ|ጋዜጣዊ\s*መግለጫ|"
    r"በዛሬው\s*ዕለት|ባለሥልጣናት|ሚኒስቴር|ፓርላማ|"
    r"ፕሬዝዳንት|ጠቅላይ\s*ሚኒስትር|የምርጫ\s*ቦርድ|"
    r"እንደዘገበው|መረጃዎች\s*ያመለክታሉ|በሰጡት\s*መግለጫ)"
)
PROMO_RE = re.compile(
    r"(subscribe|follow|share|newsletter|ሰብስክራይብ|ተከታተሉ|"
    r"ይከታተሉ|ሼር|ማስታወቂያ|ሙሉውን\s*ለማንበብ|"
    r"እዚህ\s*ክሊክ|አስተያየት\s*ይስጡ)",
    re.I,
)
URL_RE = re.compile(r"https?://\S+|www\.\S+|@\w+|#\S+", re.I)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--min-words", type=int, default=5)
    parser.add_argument("--max-words", type=int, default=50)
    parser.add_argument("--delay", type=float, default=0.35)
    return parser.parse_args()


def visible_text(markup: str) -> str:
    soup = BeautifulSoup(html.unescape(markup), "html.parser")
    for node in soup.select("script, style, nav, footer, form"):
        node.decompose()
    return soup.get_text("\n", strip=True)


def wordpress_posts(session: requests.Session, url: str, delay: float):
    page = 1
    while True:
        response = session.get(
            url,
            params={"per_page": 100, "page": page, "_fields": "content,link"},
            timeout=40,
        )
        if response.status_code == 400:
            return
        response.raise_for_status()
        posts = response.json()
        if not posts:
            return
        for post in posts:
            yield visible_text(post.get("content", {}).get("rendered", ""))
        page += 1
        time.sleep(delay)


def blogger_posts(session: requests.Session, url: str, delay: float):
    start = 1
    page_size = 150
    namespaces = {"atom": "http://www.w3.org/2005/Atom"}
    while True:
        query = urlencode(
            {
                "alt": "atom",
                "max-results": page_size,
                "start-index": start,
            }
        )
        response = session.get(f"{url}?{query}", timeout=40)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        entries = root.findall("atom:entry", namespaces)
        if not entries:
            return
        for entry in entries:
            content = entry.find("atom:content", namespaces)
            if content is not None and content.text:
                yield visible_text(content.text)
        if len(entries) < page_size:
            return
        start += page_size
        time.sleep(delay)


def filtered_sentences(text: str, sentence_filter: SentenceFilter):
    text = URL_RE.sub(" ", text)
    for raw_sentence in split_sentences(text):
        sentence = clean(raw_sentence)
        if NEWS_RE.search(sentence) or PROMO_RE.search(sentence):
            continue
        accepted, _reason = sentence_filter.passes(sentence)
        if accepted:
            yield sentence


def main() -> int:
    args = parse_args()
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
        "AmharicSentenceResearchBot/1.0 "
        "(public-blog-text-corpus; contact: natnaeltamiru98@gmail.com)"
    )

    sentences: list[str] = []
    seen: set[str] = set()
    sources = [
        *(
            (name, wordpress_posts(session, url, args.delay))
            for name, url in WORDPRESS_SOURCES
        ),
        *(
            (name, blogger_posts(session, url, args.delay))
            for name, url in BLOGGER_SOURCES
        ),
    ]
    for source_name, posts in sources:
        article_count = 0
        for article_text in posts:
            article_count += 1
            for sentence in filtered_sentences(article_text, sentence_filter):
                if sentence in seen:
                    continue
                seen.add(sentence)
                sentences.append(sentence)
                if len(sentences) >= args.limit:
                    break
            if article_count % 25 == 0:
                print(f"{source_name}: posts={article_count}, total={len(sentences)}")
            if len(sentences) >= args.limit:
                break
        print(f"{source_name}: finished posts={article_count}, total={len(sentences)}")
        if len(sentences) >= args.limit:
            break

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(f"{sentence}\n" for sentence in sentences),
        encoding="utf-8",
    )
    print(f"Wrote {len(sentences)} sentences to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
