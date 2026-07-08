from __future__ import annotations

from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from crawl.fetcher import WebFetcher
from search.base import SearchResult
from search.engines.common import build_search_fetcher, validate_search_response
from search.url_utils import clean_result_url, is_valid_company_site, normalize_domain


class DuckDuckGoEngine:
    name = "duckduckgo"

    def __init__(
        self,
        max_pages: int = 2,
        timeout: int = 20,
        sleep_range: tuple[float, float] = (2.0, 5.0),
        session: requests.Session | None = None,
        fetcher: WebFetcher | None = None,
        request_interval_seconds: float = 10.0,
        max_retries: int = 3,
        backoff_base_seconds: float = 20.0,
        backoff_max_seconds: float = 180.0,
        proxy_url: str = "",
        use_system_proxy: bool = True,
    ) -> None:
        self.max_pages = max_pages
        self.timeout = timeout
        self.sleep_range = sleep_range
        self.fetcher = fetcher or build_search_fetcher(
            session=session,
            request_interval_seconds=request_interval_seconds,
            max_retries=max_retries,
            backoff_base_seconds=backoff_base_seconds,
            backoff_max_seconds=backoff_max_seconds,
            timeout_seconds=timeout,
            proxy_url=proxy_url,
            use_system_proxy=use_system_proxy,
        )

    def search(self, keyword: str) -> list[SearchResult]:
        results: list[SearchResult] = []
        seen_domains: set[str] = set()

        for page in range(self.max_pages):
            offset = page * 30
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(keyword)}&s={offset}"
            response = self.fetcher.fetch_response(
                search_url,
                extra_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": "https://duckduckgo.com/",
                },
                response_validator=lambda item: validate_search_response(item, self.name, "a.result__a"),
            )

            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.select("a.result__a"):
                title = link.get_text(" ", strip=True)
                website = clean_result_url(link.get("href", ""))
                domain = normalize_domain(website)
                if not is_valid_company_site(website) or domain in seen_domains:
                    continue
                seen_domains.add(domain)
                results.append(
                    SearchResult(
                        keyword=keyword,
                        title=title,
                        website=website,
                        domain=domain,
                        source_url=search_url,
                        engine=self.name,
                    )
                )

        return results
