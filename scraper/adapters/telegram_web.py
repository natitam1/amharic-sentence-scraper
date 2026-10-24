from __future__ import annotations

import logging
import re
from datetime import date, datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from scraper.adapters.base_adapter import BaseAdapter
from scraper.models import RawArticle

LOGGER = logging.getLogger("amharic_scraper")

class TelegramWebAdapter(BaseAdapter):
    """Scrapes public Telegram channels via their t.me/s/ public preview pages."""

    def list_article_urls(self, since: date | None = None) -> list[str]:
        # Telegram public channels allow paginated viewing via t.me/s/channel_name
        channel = self.config.get("channel_name")
        if not channel:
            raise ValueError(f"Missing 'channel_name' in config for source {self.source_id}")

        # Clean channel name if full URL was provided
        channel = channel.strip().split('/')[-1].replace('@', '')
        
        # We start with the base public preview URL
        url = f"https://t.me/s/{channel}"
        LOGGER.info(f"Fetching Telegram channel preview: {url}")
        
        response = self.fetcher.get(url, self.config.get("delay_seconds", 3.0))
        if not response or not response.text:
            LOGGER.warning(f"Failed to fetch Telegram channel: {channel}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Telegram messages are contained in div.tgme_widget_message
        message_divs = soup.select(".tgme_widget_message")
        urls = []
        for div in message_divs:
            # Get the message link (looks like t.me/channel_name/1234)
            link_node = div.select_one("a.tgme_widget_message_date")
            if link_node and link_node.get("href"):
                msg_url = link_node["href"]
                # Filter out message link redirects
                if "/s/" not in msg_url:
                    # Rewrite to public view URL or clean URL format
                    urls.append(msg_url)
        
        # Return unique URLs
        return list(dict.fromkeys(urls))

    def fetch_article(self, url: str) -> RawArticle:
        # To get the single message details cleanly, we fetch the t.me/s/ version or just scrape the single page.
        # But we can fetch the direct embed preview or public web page: t.me/channel/id?embed=1 or t.me/s/channel?before=id+1
        # To make it super simple and reliable, we'll fetch the embed version which has clean HTML of the message.
        embed_url = url
        if "embed=1" not in url:
            embed_url = f"{url}?embed=1" if "?" not in url else f"{url}&embed=1"

        response = self.fetcher.get(embed_url, self.config.get("delay_seconds", 3.0))
        if not response or not response.text:
            raise ValueError(f"Could not load Telegram message: {url}")

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the message text
        text_node = soup.select_one(".tgme_widget_message_text")
        body_text = text_node.get_text("\n") if text_node else ""
        
        # Find the date
        date_node = soup.select_one(".tgme_widget_message_date time")
        published = None
        if date_node and date_node.get("datetime"):
            # Format: 2026-07-23T10:56:53+03:00 or similar
            dt_str = date_node["datetime"]
            try:
                published = datetime.fromisoformat(dt_str).date().isoformat()
            except Exception:
                published = dt_str[:10]

        # Extract title (first few words or channel name)
        channel_name = soup.select_one(".tgme_widget_message_author")
        title = f"Telegram Message from {channel_name.get_text().strip()}" if channel_name else "Telegram Message"

        return RawArticle(
            url=url,
            title=title,
            published_date=published,
            body_text=body_text,
            metadata={
                "channel_url": url.split("/")[3] if len(url.split("/")) > 3 else url,
            }
        )
