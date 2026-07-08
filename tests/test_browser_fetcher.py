import unittest

from crawl.browser_fetcher import BrowserFetchConfig, BrowserFetcher


class FakeScraplingResponse:
    def __init__(self, url: str, content: str, status: int = 200) -> None:
        self.url = url
        self.status = status
        self.headers = {"content-type": "text/html"}
        self.body = content.encode("utf-8")


class FakeDynamicSession:
    starts = 0
    closes = 0

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.urls: list[str] = []

    def start(self) -> None:
        type(self).starts += 1

    def close(self) -> None:
        type(self).closes += 1

    def fetch(self, url: str, **kwargs: object) -> FakeScraplingResponse:
        self.urls.append(url)
        return FakeScraplingResponse(url, "<html><a class='result__a' href='https://example.com'>Example</a></html>")


class BrowserFetcherTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeDynamicSession.starts = 0
        FakeDynamicSession.closes = 0

    def test_reuses_dynamic_session_and_returns_response_shape(self) -> None:
        sessions: list[FakeDynamicSession] = []

        def session_factory(**kwargs: object) -> FakeDynamicSession:
            session = FakeDynamicSession(**kwargs)
            sessions.append(session)
            return session

        fetcher = BrowserFetcher(
            BrowserFetchConfig(
                headless=True,
                network_idle=True,
                proxy="http://127.0.0.1:7897",
                max_retries=1,
                request_interval_seconds=0,
                respect_robots=False,
            ),
            session_factory=session_factory,
        )

        first = fetcher.fetch_response("https://html.duckduckgo.com/html/?q=one")
        second = fetcher.fetch_response("https://html.duckduckgo.com/html/?q=two")
        fetcher.close()

        self.assertEqual(len(sessions), 1)
        self.assertEqual(FakeDynamicSession.starts, 1)
        self.assertEqual(FakeDynamicSession.closes, 1)
        self.assertEqual(sessions[0].urls, ["https://html.duckduckgo.com/html/?q=one", "https://html.duckduckgo.com/html/?q=two"])
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.url, "https://html.duckduckgo.com/html/?q=two")
        self.assertIn("result__a", second.text)

    def test_retries_when_validator_rejects_browser_response(self) -> None:
        calls = {"count": 0}
        sleeps: list[float] = []

        def session_factory(**kwargs: object) -> FakeDynamicSession:
            return FakeDynamicSession(**kwargs)

        def validator(response: object) -> None:
            calls["count"] += 1
            if calls["count"] < 2:
                raise RuntimeError("blocked")

        fetcher = BrowserFetcher(
            BrowserFetchConfig(
                max_retries=2,
                backoff_base_seconds=0.5,
                request_interval_seconds=0,
                respect_robots=False,
            ),
            session_factory=session_factory,
            sleep_func=sleeps.append,
        )

        response = fetcher.fetch_response("https://example.com", response_validator=validator)
        fetcher.close()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(sleeps, [0.5])

    def test_respects_robots_before_starting_browser_session(self) -> None:
        sessions: list[FakeDynamicSession] = []

        def session_factory(**kwargs: object) -> FakeDynamicSession:
            session = FakeDynamicSession(**kwargs)
            sessions.append(session)
            return session

        fetcher = BrowserFetcher(
            BrowserFetchConfig(respect_robots=True),
            session_factory=session_factory,
            robots_allowed_func=lambda url: False,
        )

        with self.assertRaisesRegex(RuntimeError, "robots.txt"):
            fetcher.fetch_response("https://blocked.example")

        self.assertEqual(sessions, [])


if __name__ == "__main__":
    unittest.main()
