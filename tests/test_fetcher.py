import time
import unittest

from crawl.fetcher import FetcherConfig, RateLimiter, WebFetcher


class FakeResponse:
    def __init__(
        self,
        text: str,
        url: str = "https://example.com",
        status_code: int = 200,
        content_type: str = "text/html",
    ) -> None:
        self.text = text
        self.url = url
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append(url)
        if len(self.calls) < 3:
            raise RuntimeError("temporary failure")
        return FakeResponse("<html>ok</html>", url=url)


class ValidatorSession:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append(url)
        return FakeResponse("<html>challenge</html>", url=url, status_code=202)


class FetcherTests(unittest.TestCase):
    def test_retries_with_exponential_backoff_until_success(self) -> None:
        sleeps: list[float] = []
        session = FakeSession()
        fetcher = WebFetcher(
            FetcherConfig(
                max_retries=3,
                backoff_base_seconds=0.25,
                respect_robots=False,
                global_min_interval_seconds=0,
                domain_min_interval_seconds=0,
            ),
            session_factory=lambda: session,
            sleep_func=sleeps.append,
        )

        html, final_url = fetcher.fetch_html("https://example.com")

        self.assertEqual(html, "<html>ok</html>")
        self.assertEqual(final_url, "https://example.com")
        self.assertEqual(len(session.calls), 3)
        self.assertEqual(sleeps, [0.25, 0.5])

    def test_retries_when_response_validator_reports_block(self) -> None:
        sleeps: list[float] = []
        session = ValidatorSession()
        attempts = {"count": 0}

        def validator(response: FakeResponse) -> None:
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise RuntimeError("blocked")

        fetcher = WebFetcher(
            FetcherConfig(
                max_retries=3,
                backoff_base_seconds=0.25,
                respect_robots=False,
                global_min_interval_seconds=0,
                domain_min_interval_seconds=0,
            ),
            session_factory=lambda: session,
            sleep_func=sleeps.append,
        )

        response = fetcher.fetch_response("https://example.com", response_validator=validator)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(session.calls), 3)
        self.assertEqual(sleeps, [0.25, 0.5])

    def test_rate_limiter_enforces_global_and_domain_intervals(self) -> None:
        now = [100.0]
        sleeps: list[float] = []

        def monotonic() -> float:
            return now[0]

        def sleep(seconds: float) -> None:
            sleeps.append(round(seconds, 3))
            now[0] += seconds

        limiter = RateLimiter(
            global_min_interval_seconds=0.5,
            domain_min_interval_seconds=1.0,
            monotonic_func=monotonic,
            sleep_func=sleep,
        )

        limiter.wait("example.com")
        limiter.wait("other.example")
        limiter.wait("example.com")

        self.assertEqual(sleeps, [0.5, 0.5])


if __name__ == "__main__":
    unittest.main()
