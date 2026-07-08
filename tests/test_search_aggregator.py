import unittest
import threading

from search.aggregator import SearchAggregator
from search.base import SearchResult


class StaticEngine:
    def __init__(self, name: str, results: list[SearchResult]) -> None:
        self.name = name
        self._results = results

    def search(self, keyword: str) -> list[SearchResult]:
        return self._results


class FailingEngine:
    name = "broken"

    def search(self, keyword: str) -> list[SearchResult]:
        raise RuntimeError("upstream unavailable")


class SearchAggregatorTests(unittest.TestCase):
    def test_deduplicates_by_domain_and_keeps_engine_errors_isolated(self) -> None:
        aggregator = SearchAggregator(
            engines=[
                StaticEngine(
                    "first",
                    [
                        SearchResult(
                            keyword="heat pump Turkey",
                            title="Example A",
                            website="https://www.example.com/a",
                            source_url="https://search.local/a",
                            engine="first",
                        )
                    ],
                ),
                FailingEngine(),
                StaticEngine(
                    "second",
                    [
                        SearchResult(
                            keyword="heat pump Turkey",
                            title="Example duplicate",
                            website="http://example.com/b",
                            source_url="https://search.local/b",
                            engine="second",
                        ),
                        SearchResult(
                            keyword="heat pump Turkey",
                            title="Vendor",
                            website="https://vendor.example/about",
                            source_url="https://search.local/c",
                            engine="second",
                        ),
                    ],
                ),
            ],
            max_workers=3,
        )

        batch = aggregator.search_keyword("heat pump Turkey")

        self.assertEqual({result.domain for result in batch.results}, {"example.com", "vendor.example"})
        self.assertEqual(len(batch.results), 2)
        self.assertIn("broken", batch.errors)
        self.assertIn("upstream unavailable", batch.errors["broken"])

    def test_single_worker_runs_engine_in_current_thread(self) -> None:
        caller_thread = threading.get_ident()
        seen_threads: list[int] = []

        class ThreadRecordingEngine:
            name = "thread-recorder"

            def search(self, keyword: str) -> list[SearchResult]:
                seen_threads.append(threading.get_ident())
                return []

        aggregator = SearchAggregator(engines=[ThreadRecordingEngine()], max_workers=1)

        aggregator.search_keyword("heat pump Turkey")

        self.assertEqual(seen_threads, [caller_thread])


if __name__ == "__main__":
    unittest.main()
