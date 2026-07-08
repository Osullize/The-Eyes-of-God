from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

from crawl.fetcher import RateLimiter


@dataclass
class BrowserFetchConfig:
    headless: bool = True
    network_idle: bool = True
    proxy: str = ""
    timeout_ms: int = 30000
    wait_ms: int = 0
    max_pages: int = 1
    max_retries: int = 2
    backoff_base_seconds: float = 10.0
    backoff_max_seconds: float = 120.0
    request_interval_seconds: float = 10.0
    disable_resources: bool = False
    block_ads: bool = False
    useragent: str = ""
    respect_robots: bool = True


@dataclass(frozen=True)
class BrowserFetchResponse:
    text: str
    url: str
    status_code: int
    headers: dict[str, str]


class BrowserFetcher:
    """Scrapling DynamicSession wrapper with a persistent browser context."""

    def __init__(
        self,
        config: BrowserFetchConfig | None = None,
        session_factory: Callable[..., object] | None = None,
        sleep_func: Callable[[float], None] = time.sleep,
        robots_allowed_func: Callable[[str], bool] | None = None,
    ) -> None:
        self.config = config or BrowserFetchConfig()
        self.session_factory = session_factory
        self.sleep = sleep_func
        self.robots_allowed_func = robots_allowed_func
        self.rate_limiter = RateLimiter(
            global_min_interval_seconds=0.0,
            domain_min_interval_seconds=self.config.request_interval_seconds,
            sleep_func=sleep_func,
        )
        self._session: object | None = None
        self._session_lock = threading.RLock()
        self._fetch_lock = threading.Lock()
        self._robots_lock = threading.Lock()
        self._robots_cache: dict[str, RobotFileParser] = {}

    def _domain(self, url: str) -> str:
        domain = urlparse(url).netloc.lower()
        if ":" in domain:
            domain = domain.split(":", 1)[0]
        return domain.removeprefix("www.")

    def _make_session(self) -> object:
        kwargs: dict[str, object] = {
            "headless": self.config.headless,
            "network_idle": self.config.network_idle,
            "timeout": self.config.timeout_ms,
            "wait": self.config.wait_ms,
            "max_pages": self.config.max_pages,
            "disable_resources": self.config.disable_resources,
            "block_ads": self.config.block_ads,
            "google_search": False,
            "retries": 1,
        }
        if self.config.proxy:
            kwargs["proxy"] = self.config.proxy
        if self.config.useragent:
            kwargs["useragent"] = self.config.useragent

        if self.session_factory is not None:
            return self.session_factory(**kwargs)

        from scrapling.fetchers import DynamicSession

        return DynamicSession(**kwargs)

    def _robot_cache_key(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc.lower()}"

    def _load_robot_parser(self, url: str) -> RobotFileParser:
        cache_key = self._robot_cache_key(url)
        with self._robots_lock:
            cached = self._robots_cache.get(cache_key)
            if cached is not None:
                return cached

        parser = RobotFileParser()
        robots_url = urljoin(cache_key, "/robots.txt")
        parser.set_url(robots_url)
        try:
            domain = self._domain(robots_url)
            with self.rate_limiter.limit(domain):
                response = requests.get(robots_url, timeout=(8, 20))
            if response.status_code >= 400:
                parser.allow_all = True
            else:
                parser.parse(response.text.splitlines())
        except Exception:
            parser.allow_all = True

        with self._robots_lock:
            self._robots_cache[cache_key] = parser
        return parser

    def _allowed_by_robots(self, url: str) -> bool:
        if not self.config.respect_robots:
            return True
        if self.robots_allowed_func is not None:
            return self.robots_allowed_func(url)
        return self._load_robot_parser(url).can_fetch("*", url)

    def _ensure_session(self) -> object:
        with self._session_lock:
            if self._session is None:
                self._session = self._make_session()
                start = getattr(self._session, "start", None)
                if callable(start):
                    start()
            return self._session

    def _response_text(self, response: object) -> str:
        body = getattr(response, "body", b"")
        if callable(body):
            body = body()
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")
        if isinstance(body, str):
            return body
        html_content = getattr(response, "html_content", None)
        if html_content:
            return str(html_content)
        return str(response)

    def _normalize_response(self, response: object, fallback_url: str) -> BrowserFetchResponse:
        headers = getattr(response, "headers", {}) or {}
        return BrowserFetchResponse(
            text=self._response_text(response),
            url=str(getattr(response, "url", fallback_url)),
            status_code=int(getattr(response, "status", getattr(response, "status_code", 0)) or 0),
            headers={str(key): str(value) for key, value in dict(headers).items()},
        )

    def fetch_response(
        self,
        url: str,
        extra_headers: dict[str, str] | None = None,
        response_validator: Callable[[BrowserFetchResponse], None] | None = None,
    ) -> BrowserFetchResponse:
        if not self._allowed_by_robots(url):
            raise RuntimeError(f"Blocked by robots.txt: {url}")

        last_error: Exception | None = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                session = self._ensure_session()
                domain = self._domain(url)
                with self._fetch_lock:
                    with self.rate_limiter.limit(domain):
                        response = session.fetch(
                            url,
                            extra_headers=extra_headers or {},
                            network_idle=self.config.network_idle,
                            timeout=self.config.timeout_ms,
                            wait=self.config.wait_ms,
                            disable_resources=self.config.disable_resources,
                        )
                normalized = self._normalize_response(response, url)
                if response_validator:
                    response_validator(normalized)
                return normalized
            except Exception as error:
                last_error = error
                if attempt >= self.config.max_retries:
                    break
                delay = min(
                    self.config.backoff_max_seconds,
                    self.config.backoff_base_seconds * (2 ** (attempt - 1)),
                )
                self.sleep(delay)

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"Unable to fetch URL with browser: {url}")

    def fetch_html(self, url: str) -> tuple[str, str]:
        response = self.fetch_response(url)
        return response.text, response.url

    def close(self) -> None:
        with self._session_lock:
            if self._session is not None:
                close = getattr(self._session, "close", None)
                if callable(close):
                    close()
                self._session = None
