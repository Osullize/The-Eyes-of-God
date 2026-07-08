from __future__ import annotations

from bs4 import BeautifulSoup

from crawl.fetcher import FetcherConfig, USER_AGENTS, WebFetcher
from search.base import SearchBlockedError


BLOCKED_TEXT_MARKERS = [
    "captcha",
    "unusual traffic",
    "unusual activity",
    "verify you are human",
    "verification",
    "challenge",
    "anomaly",
    "automated requests",
    "sorry, we can't serve this request",
]


def build_search_fetcher(
    session: object | None,
    request_interval_seconds: float,
    max_retries: int,
    backoff_base_seconds: float,
    backoff_max_seconds: float,
    timeout_seconds: float,
    proxy_url: str = "",
    use_system_proxy: bool = True,
) -> WebFetcher:
    session_factory = (lambda: session) if session is not None else None
    return WebFetcher(
        FetcherConfig(
            max_retries=max_retries,
            backoff_base_seconds=backoff_base_seconds,
            backoff_max_seconds=backoff_max_seconds,
            timeout_connect_seconds=min(8.0, timeout_seconds),
            timeout_read_seconds=timeout_seconds,
            global_min_interval_seconds=0.0,
            domain_min_interval_seconds=request_interval_seconds,
            use_system_proxy=use_system_proxy,
            proxy_url=proxy_url,
            respect_robots=False,
            user_agents=list(USER_AGENTS),
        ),
        session_factory=session_factory,
    )


def validate_search_response(response: object, engine_name: str, result_selector: str) -> None:
    status_code = getattr(response, "status_code", 0)
    text = getattr(response, "text", "") or ""
    lower_text = text.lower()

    if status_code == 202:
        raise SearchBlockedError(f"{engine_name} returned HTTP 202 challenge/throttle page")

    for marker in BLOCKED_TEXT_MARKERS:
        if marker in lower_text:
            raise SearchBlockedError(f"{engine_name} returned blocked/challenge page marker: {marker}")

    soup = BeautifulSoup(text, "html.parser")
    if not soup.select(result_selector):
        raise SearchBlockedError(f"{engine_name} response has no result blocks: {result_selector}")
