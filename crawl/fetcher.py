from __future__ import annotations

import random
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Iterator
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
]


@dataclass
class FetcherConfig:
    max_retries: int = 3
    backoff_base_seconds: float = 1.0
    backoff_max_seconds: float = 30.0
    timeout_connect_seconds: float = 8.0
    timeout_read_seconds: float = 30.0
    global_min_interval_seconds: float = 0.2
    domain_min_interval_seconds: float = 1.0
    use_system_proxy: bool = True
    proxy_url: str = ""
    respect_robots: bool = True
    user_agents: list[str] = field(default_factory=lambda: list(USER_AGENTS))


class RateLimiter:
    def __init__(
        self,
        global_min_interval_seconds: float,
        domain_min_interval_seconds: float,
        monotonic_func: Callable[[], float] = time.monotonic,
        sleep_func: Callable[[float], None] = time.sleep,
    ) -> None:
        self.global_min_interval_seconds = max(0.0, global_min_interval_seconds)
        self.domain_min_interval_seconds = max(0.0, domain_min_interval_seconds)
        self.monotonic = monotonic_func
        self.sleep = sleep_func
        self._global_lock = threading.Lock()
        self._domain_locks_guard = threading.Lock()
        self._domain_locks: dict[str, threading.Lock] = {}
        self._last_global_request = 0.0
        self._last_domain_request: dict[str, float] = {}

    def _domain_lock(self, domain: str) -> threading.Lock:
        with self._domain_locks_guard:
            if domain not in self._domain_locks:
                self._domain_locks[domain] = threading.Lock()
            return self._domain_locks[domain]

    def _sleep_until_interval(self, last_time: float, min_interval: float) -> None:
        if last_time <= 0 or min_interval <= 0:
            return
        elapsed = self.monotonic() - last_time
        if elapsed < min_interval:
            self.sleep(min_interval - elapsed)

    def wait(self, domain: str) -> None:
        normalized_domain = domain.lower()
        with self._global_lock:
            self._sleep_until_interval(self._last_global_request, self.global_min_interval_seconds)
            self._last_global_request = self.monotonic()

        last_domain_request = self._last_domain_request.get(normalized_domain, 0.0)
        self._sleep_until_interval(last_domain_request, self.domain_min_interval_seconds)
        self._last_domain_request[normalized_domain] = self.monotonic()

    @contextmanager
    def limit(self, domain: str) -> Iterator[None]:
        domain_lock = self._domain_lock(domain.lower())
        with domain_lock:
            self.wait(domain)
            yield


class RobotsDeniedError(RuntimeError):
    pass


class WebFetcher:
    def __init__(
        self,
        config: FetcherConfig | None = None,
        session_factory: Callable[[], requests.Session] | None = None,
        sleep_func: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config or FetcherConfig()
        self.session_factory = session_factory or requests.Session
        self.sleep = sleep_func
        self.rate_limiter = RateLimiter(
            global_min_interval_seconds=self.config.global_min_interval_seconds,
            domain_min_interval_seconds=self.config.domain_min_interval_seconds,
            sleep_func=sleep_func,
        )
        self._local = threading.local()
        self._robots_lock = threading.Lock()
        self._robots_cache: dict[str, RobotFileParser] = {}

    def _session(self) -> requests.Session:
        session = getattr(self._local, "session", None)
        if session is None:
            session = self.session_factory()
            session.trust_env = self.config.use_system_proxy
            self._local.session = session
        return session

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(self.config.user_agents),
            "Accept-Language": "en-US,en;q=0.9,tr;q=0.8,de;q=0.7",
        }

    def _proxies(self) -> dict[str, str] | None:
        if not self.config.proxy_url:
            return None
        return {"http": self.config.proxy_url, "https": self.config.proxy_url}

    def _domain(self, url: str) -> str:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if ":" in domain:
            domain = domain.split(":", 1)[0]
        return domain.removeprefix("www.")

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
                response = self._session().get(
                    robots_url,
                    headers=self._headers(),
                    timeout=(self.config.timeout_connect_seconds, self.config.timeout_read_seconds),
                    allow_redirects=True,
                    proxies=self._proxies(),
                )
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
        parser = self._load_robot_parser(url)
        return parser.can_fetch("*", url)

    def fetch_response(
        self,
        url: str,
        extra_headers: dict[str, str] | None = None,
        response_validator: Callable[[requests.Response], None] | None = None,
    ) -> requests.Response:
        if not self._allowed_by_robots(url):
            raise RobotsDeniedError(f"Blocked by robots.txt: {url}")

        last_error: Exception | None = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                domain = self._domain(url)
                headers = self._headers()
                if extra_headers:
                    headers.update(extra_headers)
                with self.rate_limiter.limit(domain):
                    response = self._session().get(
                        url,
                        headers=headers,
                        timeout=(self.config.timeout_connect_seconds, self.config.timeout_read_seconds),
                        allow_redirects=True,
                        proxies=self._proxies(),
                    )
                response.raise_for_status()
                if response_validator:
                    response_validator(response)
                return response
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
        raise RuntimeError(f"Unable to fetch URL: {url}")

    def fetch_html(self, url: str) -> tuple[str, str]:
        response = self.fetch_response(url)
        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return "", response.url
        return response.text, response.url
