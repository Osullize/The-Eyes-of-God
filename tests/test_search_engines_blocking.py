import unittest

from search.base import SearchBlockedError
from search.engines.bing import BingEngine
from search.engines.duckduckgo import DuckDuckGoEngine


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200, url: str = "https://search.local") -> None:
        self.text = text
        self.status_code = status_code
        self.url = url
        self.headers = {"Content-Type": "text/html"}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeFetcher:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response

    def fetch_response(self, url: str, **kwargs: object) -> FakeResponse:
        validator = kwargs.get("response_validator")
        if validator:
            validator(self.response)
        return self.response


class SearchEngineBlockingTests(unittest.TestCase):
    def test_duckduckgo_treats_http_202_as_blocked(self) -> None:
        engine = DuckDuckGoEngine(max_pages=1, fetcher=FakeFetcher(FakeResponse("challenge", status_code=202)))

        with self.assertRaises(SearchBlockedError):
            engine.search("heat pump Turkey")

    def test_duckduckgo_treats_missing_result_blocks_as_blocked(self) -> None:
        engine = DuckDuckGoEngine(max_pages=1, fetcher=FakeFetcher(FakeResponse("<html>No anchors</html>")))

        with self.assertRaises(SearchBlockedError):
            engine.search("heat pump Turkey")

    def test_bing_treats_unusual_traffic_page_as_blocked(self) -> None:
        engine = BingEngine(
            max_pages=1,
            fetcher=FakeFetcher(FakeResponse("<html>unusual traffic captcha</html>")),
        )

        with self.assertRaises(SearchBlockedError):
            engine.search("heat pump Turkey")


if __name__ == "__main__":
    unittest.main()
