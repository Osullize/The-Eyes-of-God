import unittest
import csv
import tempfile
import textwrap
from pathlib import Path

from config.keywords import KeywordSpec
from run_search import aggregate_domain_rows, build_parser, resolve_search_run_config, run_search
from search.base import SearchResult


class RunSearchAggregationTests(unittest.TestCase):
    def test_same_domain_keeps_all_matched_keywords_and_industries(self) -> None:
        heat_spec = KeywordSpec(
            keyword="heat pump installer Turkey",
            country="Turkey",
            country_term="Turkey",
            industry="heat_pump",
            industry_term="heat pump installer",
        )
        hvac_spec = KeywordSpec(
            keyword="HVAC contractor Turkey",
            country="Turkey",
            country_term="Turkey",
            industry="hvac",
            industry_term="HVAC contractor",
        )
        rows_by_domain: dict[str, dict[str, str]] = {}

        aggregate_domain_rows(
            rows_by_domain,
            SearchResult(
                keyword=heat_spec.keyword,
                title="Acme",
                website="https://www.example.com/heat",
                source_url="https://search.local/1",
                engine="duckduckgo",
            ),
            heat_spec,
        )
        aggregate_domain_rows(
            rows_by_domain,
            SearchResult(
                keyword=hvac_spec.keyword,
                title="Acme HVAC",
                website="https://example.com/hvac",
                source_url="https://search.local/2",
                engine="bing",
            ),
            hvac_spec,
        )

        self.assertEqual(list(rows_by_domain), ["example.com"])
        row = rows_by_domain["example.com"]
        self.assertEqual(row["keyword"], "heat pump installer Turkey")
        self.assertEqual(row["matched_keywords"], "heat pump installer Turkey; HVAC contractor Turkey")
        self.assertEqual(row["matched_industries"], "heat_pump; hvac")
        self.assertEqual(row["matched_industry_terms"], "heat pump installer; HVAC contractor")

    def test_run_search_writes_after_each_keyword_and_records_failed_keyword(self) -> None:
        class FirstKeywordOnlyEngine:
            name = "fixture"

            def search(self, keyword: str) -> list[SearchResult]:
                if keyword == "first Turkey":
                    return [
                        SearchResult(
                            keyword=keyword,
                            title="First Co",
                            website="https://first.example",
                            source_url="https://search.local/first",
                            engine=self.name,
                        )
                    ]
                raise RuntimeError("blocked")

        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            config_path = base / "keywords.yaml"
            output_path = base / "company_websites.csv"
            state_dir = base / "state"
            config_path.write_text(
                textwrap.dedent(
                    """
                    countries:
                      Turkey:
                        terms:
                          - Turkey
                    industries:
                      first:
                        terms:
                          - first
                      second:
                        terms:
                          - second
                    """
                ).strip(),
                encoding="utf-8",
            )

            rows = run_search(
                config_path=config_path,
                output_file=output_path,
                engines=[FirstKeywordOnlyEngine()],
                state_dir=state_dir,
                keyword_delay_seconds=0,
            )

            with output_path.open("r", encoding="utf-8-sig", newline="") as file:
                written = list(csv.DictReader(file))

            self.assertEqual(len(rows), 1)
            self.assertEqual(len(written), 1)
            self.assertEqual(written[0]["domain"], "first.example")
            self.assertEqual((state_dir / "completed_keywords.txt").read_text(encoding="utf-8").strip(), "first Turkey")
            self.assertIn("second Turkey", (state_dir / "failed_keywords.csv").read_text(encoding="utf-8-sig"))

    def test_run_search_allows_database_native_mode_without_csv_output(self) -> None:
        class FixtureEngine:
            name = "fixture"

            def search(self, keyword: str) -> list[SearchResult]:
                return [
                    SearchResult(
                        keyword=keyword,
                        title="Acme",
                        website="https://acme.example",
                        source_url="https://search.local",
                        engine=self.name,
                    )
                ]

        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            config_path = base / "keywords.yaml"
            state_dir = base / "state"
            config_path.write_text(
                textwrap.dedent(
                    """
                    countries:
                      France:
                        terms:
                          - France
                    industries:
                      pool:
                        terms:
                          - pool heat pump
                    """
                ).strip(),
                encoding="utf-8",
            )

            rows = run_search(
                config_path=config_path,
                output_file=None,
                engines=[FixtureEngine()],
                state_dir=state_dir,
                keyword_delay_seconds=0,
            )

            csv_files = list(base.glob("*.csv"))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["domain"], "acme.example")
        self.assertEqual(csv_files, [])

    def test_run_search_accepts_direct_keyword_specs(self) -> None:
        class RecordingEngine:
            name = "fixture"

            def __init__(self) -> None:
                self.keywords: list[str] = []

            def search(self, keyword: str) -> list[SearchResult]:
                self.keywords.append(keyword)
                return [
                    SearchResult(
                        keyword=keyword,
                        title="Acme",
                        website="https://acme.example",
                        source_url="https://search.local",
                        engine=self.name,
                    )
                ]

        with tempfile.TemporaryDirectory() as temp_dir:
            engine = RecordingEngine()
            rows = run_search(
                config_path=Path(temp_dir) / "missing.yaml",
                output_file=None,
                engines=[engine],
                state_dir=Path(temp_dir) / "state",
                keyword_delay_seconds=0,
                keyword_specs=[
                    KeywordSpec(
                        keyword="pool heat pump France",
                        country="France",
                        country_term="France",
                        industry="France Pool",
                        industry_term="pool heat pump",
                    )
                ],
            )

        self.assertEqual(engine.keywords, ["pool heat pump France"])
        self.assertEqual(rows[0]["country"], "France")
        self.assertEqual(rows[0]["industry"], "France Pool")

    def test_run_search_can_disable_state_and_report_keyword_progress(self) -> None:
        class FixtureEngine:
            name = "fixture"

            def search(self, keyword: str) -> list[SearchResult]:
                return [
                    SearchResult(
                        keyword=keyword,
                        title="Acme",
                        website="https://acme.example",
                        source_url="https://search.local",
                        engine=self.name,
                    )
                ]

        events = []

        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            rows = run_search(
                config_path=base / "missing.yaml",
                output_file=None,
                engines=[FixtureEngine()],
                state_dir=None,
                keyword_delay_seconds=0,
                keyword_specs=[
                    KeywordSpec(
                        keyword="pool heat pump France",
                        country="France",
                        country_term="France",
                        industry="France Pool",
                        industry_term="pool heat pump",
                    )
                ],
                on_keyword_done=lambda event: events.append(event),
            )

            state_dirs = list(base.glob(".search_state*"))

        self.assertEqual(rows[0]["domain"], "acme.example")
        self.assertEqual(state_dirs, [])
        self.assertEqual(events[0]["keyword"], "pool heat pump France")
        self.assertEqual(events[0]["status"], "success")
        self.assertEqual(events[0]["added"], 1)

    def test_run_search_stops_before_next_keyword_when_cancel_requested(self) -> None:
        class RecordingEngine:
            name = "fixture"

            def __init__(self) -> None:
                self.keywords: list[str] = []

            def search(self, keyword: str) -> list[SearchResult]:
                self.keywords.append(keyword)
                return [
                    SearchResult(
                        keyword=keyword,
                        title="Acme",
                        website=f"https://{len(self.keywords)}.example",
                        source_url="https://search.local",
                        engine=self.name,
                    )
                ]

        engine = RecordingEngine()

        rows = run_search(
            output_file=None,
            engines=[engine],
            state_dir=None,
            keyword_delay_seconds=0,
            keyword_specs=[
                KeywordSpec(
                    keyword="first Italy",
                    country="Italy",
                    country_term="Italy",
                    industry="pool",
                    industry_term="pool heat pump",
                ),
                KeywordSpec(
                    keyword="second Italy",
                    country="Italy",
                    country_term="Italy",
                    industry="pool",
                    industry_term="pool heat pump",
                ),
            ],
            should_cancel=lambda: len(engine.keywords) >= 1,
        )

        self.assertEqual(engine.keywords, ["first Italy"])
        self.assertEqual([row["domain"] for row in rows], ["1.example"])

    def test_run_search_skips_completed_keywords_on_resume(self) -> None:
        class RecordingEngine:
            name = "fixture"

            def __init__(self) -> None:
                self.keywords: list[str] = []

            def search(self, keyword: str) -> list[SearchResult]:
                self.keywords.append(keyword)
                return []

        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            config_path = base / "keywords.yaml"
            state_dir = base / "state"
            config_path.write_text(
                textwrap.dedent(
                    """
                    countries:
                      Turkey:
                        terms:
                          - Turkey
                    industries:
                      first:
                        terms:
                          - first
                      second:
                        terms:
                          - second
                    """
                ).strip(),
                encoding="utf-8",
            )
            state_dir.mkdir()
            (state_dir / "completed_keywords.txt").write_text("first Turkey\n", encoding="utf-8")
            engine = RecordingEngine()

            run_search(
                config_path=config_path,
                output_file=base / "company_websites.csv",
                engines=[engine],
                state_dir=state_dir,
                keyword_delay_seconds=0,
            )

        self.assertEqual(engine.keywords, ["second Turkey"])

    def test_cli_exposes_browser_backend_options(self) -> None:
        args = build_parser().parse_args(
            [
                "--backend",
                "browser",
                "--headless",
                "--browser-max-pages",
                "1",
                "--proxy",
                "http://127.0.0.1:7897",
                "--database-url",
                "sqlite:///leadgen.db",
                "--no-persist-to-database",
            ]
        )

        self.assertEqual(args.backend, "browser")
        self.assertTrue(args.headless)
        self.assertEqual(args.browser_max_pages, 1)
        self.assertEqual(args.proxy, "http://127.0.0.1:7897")
        self.assertEqual(args.database_url, "sqlite:///leadgen.db")
        self.assertFalse(args.persist_to_database)

    def test_search_config_supplies_defaults_and_cli_overrides_them(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "search.yaml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    engines:
                      - duckduckgo
                      - bing
                    max_pages: 4
                    keyword_delay: 5
                    backend: browser
                    headless: false
                    use_system_proxy: true
                    """
                ).strip(),
                encoding="utf-8",
            )

            args = build_parser().parse_args(
                [
                    "--search-config",
                    str(config_path),
                    "--engines",
                    "duckduckgo",
                    "--max-pages",
                    "1",
                    "--no-system-proxy",
                ]
            )

            config = resolve_search_run_config(args)

        self.assertEqual(config.engines, ("duckduckgo",))
        self.assertEqual(config.max_pages, 1)
        self.assertEqual(config.keyword_delay, 5.0)
        self.assertEqual(config.backend, "browser")
        self.assertFalse(config.headless)
        self.assertFalse(config.use_system_proxy)


if __name__ == "__main__":
    unittest.main()
