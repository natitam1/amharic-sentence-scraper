from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

LOGGER = logging.getLogger(__name__)


@dataclass
class _RobotsEntry:
    parser: RobotFileParser | None
    fetched_at: float


class PoliteFetcher:
    def __init__(self, config: dict):
        self.user_agent = config["user_agent"]
        http = config["http"]
        self.timeout = float(http["timeout_seconds"])
        self.retries = int(http["retries"])
        self.backoff = float(http["backoff_seconds"])
        self.default_delay = float(http["default_delay_seconds"])
        self.robots_config = http.get("robots", {})
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, _RobotsEntry] = {}
        self._lock = threading.Lock()

    def _origin(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _robots_parser(self, url: str) -> RobotFileParser | None:
        origin = self._origin(url)
        ttl = float(self.robots_config.get("cache_seconds", 86400))
        cached = self._robots.get(origin)
        if cached and time.monotonic() - cached.fetched_at < ttl:
            return cached.parser

        robots_url = f"{origin}/robots.txt"
        parser: RobotFileParser | None = None
        try:
            response = self._request(robots_url, delay=0, check_robots=False)
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(response.text.splitlines())
        except requests.RequestException as exc:
            LOGGER.warning("Could not establish robots policy for %s: %s", origin, exc)
        self._robots[origin] = _RobotsEntry(parser, time.monotonic())
        return parser

    def allowed(self, url: str) -> bool:
        if not self.robots_config.get("enabled", True):
            return True
        parser = self._robots_parser(url)
        if parser is None:
            return not self.robots_config.get("fail_closed", True)
        return parser.can_fetch(self.user_agent, url)

    def get(self, url: str, delay: float | None = None) -> requests.Response:
        if not self.allowed(url):
            raise PermissionError(f"robots.txt disallows fetching {url}")
        return self._request(url, self.default_delay if delay is None else delay, False)

    def _request(
        self, url: str, delay: float, check_robots: bool = False
    ) -> requests.Response:
        domain = urlparse(url).netloc.lower()
        for attempt in range(self.retries):
            with self._lock:
                elapsed = time.monotonic() - self._last_request.get(domain, 0)
                if elapsed < delay:
                    time.sleep(delay - elapsed)
                self._last_request[domain] = time.monotonic()
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException:
                if attempt + 1 == self.retries:
                    raise
                time.sleep(self.backoff * (2**attempt))
        raise RuntimeError("unreachable")

