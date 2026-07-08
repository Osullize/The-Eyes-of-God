from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from search.url_utils import normalize_domain


@dataclass
class SearchResult:
    keyword: str
    title: str
    website: str
    source_url: str
    engine: str
    domain: str = ""

    def __post_init__(self) -> None:
        if not self.domain:
            self.domain = normalize_domain(self.website)


@dataclass
class SearchBatch:
    keyword: str
    results: list[SearchResult]
    errors: dict[str, str]


class SearchEngine(Protocol):
    name: str

    def search(self, keyword: str) -> list[SearchResult]:
        ...


class SearchBlockedError(RuntimeError):
    """Raised when a search engine returns a challenge, captcha, or throttle page."""
