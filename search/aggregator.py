from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from search.base import SearchBatch, SearchEngine, SearchResult
from search.url_utils import is_valid_company_site, normalize_domain


class SearchAggregator:
    def __init__(self, engines: list[SearchEngine], max_workers: int | None = None) -> None:
        if not engines:
            raise ValueError("At least one search engine is required")
        self.engines = engines
        self.max_workers = max_workers or len(engines)

    def search_keyword(self, keyword: str) -> SearchBatch:
        results: list[SearchResult] = []
        errors: dict[str, str] = {}
        seen_domains: set[str] = set()

        def collect_engine_results(engine: SearchEngine, engine_results: list[SearchResult]) -> None:
            for item in engine_results:
                if not is_valid_company_site(item.website):
                    continue
                item.domain = item.domain or normalize_domain(item.website)
                if item.domain in seen_domains:
                    continue
                seen_domains.add(item.domain)
                results.append(item)

        if self.max_workers <= 1:
            for engine in self.engines:
                try:
                    collect_engine_results(engine, engine.search(keyword))
                except Exception as error:
                    errors[engine.name] = str(error)
            return SearchBatch(keyword=keyword, results=results, errors=errors)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_engine = {executor.submit(engine.search, keyword): engine for engine in self.engines}
            for future in as_completed(future_to_engine):
                engine = future_to_engine[future]
                try:
                    engine_results = future.result()
                except Exception as error:
                    errors[engine.name] = str(error)
                    continue

                collect_engine_results(engine, engine_results)

        return SearchBatch(keyword=keyword, results=results, errors=errors)
