import csv
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from pipeline.state import CrawlState
from run_crawl import CompanyInput, build_parser, resolve_workers, run_crawl, select_companies


class FakeFetcher:
    def __init__(self) -> None:
        self.urls: list[str] = []
        self.closed = False

    def fetch_html(self, url: str) -> tuple[str, str]:
        self.urls.append(url)
        return (
            """
            <html>
              <head><title>Acme HVAC</title><meta name="description" content="HVAC contractor"></head>
              <body><p>Email: sales@example.com</p></body>
            </html>
            """,
            url,
        )

    def close(self) -> None:
        self.closed = True


class RunCrawlTests(unittest.TestCase):
    def test_cli_defaults_profile_input_dir_to_empty_database_first_mode(self) -> None:
        args = build_parser().parse_args([])

        self.assertEqual(args.profile_input_dir, "")

    def test_cli_exposes_depth_page_and_concurrency_controls(self) -> None:
        args = build_parser().parse_args(
            [
                "--max-depth",
                "3",
                "--max-pages-per-site",
                "20",
                "--workers",
                "5",
                "--profile-input-dir",
                "profile_inputs",
                "--profile-page-char-limit",
                "1200",
                "--retry-failed",
                "--no-robots",
            ]
        )

        self.assertEqual(args.max_depth, 3)
        self.assertEqual(args.max_pages_per_site, 20)
        self.assertEqual(args.workers, 5)
        self.assertEqual(args.profile_input_dir, "profile_inputs")
        self.assertEqual(args.profile_page_char_limit, 1200)
        self.assertTrue(args.retry_failed)
        self.assertFalse(args.respect_robots)

    def test_cli_exposes_browser_backend_controls_and_resolves_low_default_workers(self) -> None:
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
        self.assertEqual(resolve_workers(args.backend, args.workers), 1)
        self.assertEqual(resolve_workers("browser", 5), 1)
        self.assertEqual(resolve_workers("requests", None), 4)

    def test_select_companies_skips_completed_and_can_retry_failed_only(self) -> None:
        companies = [
            CompanyInput(keyword="", title="", website="https://done.example", domain="done.example"),
            CompanyInput(keyword="", title="", website="https://fail.example", domain="fail.example"),
            CompanyInput(keyword="", title="", website="https://new.example", domain="new.example"),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            state = CrawlState(Path(temp_dir))
            state.mark_completed("done.example")
            state.mark_failed("fail.example", "timeout")

            normal = select_companies(companies, state, retry_failed_only=False)
            failed_only = select_companies(companies, state, retry_failed_only=True)

        self.assertEqual([company.domain for company in normal], ["fail.example", "new.example"])
        self.assertEqual([company.domain for company in failed_only], ["fail.example"])

    def test_run_crawl_uses_and_closes_injected_fetcher(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            input_file = base / "company_websites.csv"
            output_file = base / "company_info.csv"
            state_dir = base / "state"
            with input_file.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["keyword", "title", "website", "domain"])
                writer.writeheader()
                writer.writerow(
                    {
                        "keyword": "HVAC Turkey",
                        "title": "Acme",
                        "website": "https://acme.example",
                        "domain": "acme.example",
                    }
                )
            fetcher = FakeFetcher()

            rows = run_crawl(
                input_file=input_file,
                output_file=output_file,
                state_dir=state_dir,
                workers=1,
                max_depth=0,
                max_pages_per_site=1,
                fetcher=fetcher,
            )

        self.assertTrue(fetcher.closed)
        self.assertEqual(fetcher.urls, ["https://acme.example"])
        self.assertEqual(rows[0]["status"], "success")
        self.assertIn("sales@example.com", rows[0]["emails"])

    def test_run_crawl_allows_database_native_mode_without_csv_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            state_dir = base / "state"
            fetcher = FakeFetcher()

            rows = run_crawl(
                output_file=None,
                state_dir=state_dir,
                workers=1,
                max_depth=0,
                max_pages_per_site=1,
                fetcher=fetcher,
                companies=[
                    CompanyInput(
                        keyword="pool heat pump France",
                        title="Acme",
                        website="https://acme.example",
                        domain="acme.example",
                        country="France",
                    )
                ],
            )

            csv_files = list(base.glob("*.csv"))

        self.assertEqual(rows[0]["status"], "success")
        self.assertEqual(csv_files, [])

    def test_run_crawl_can_disable_state_and_report_domain_progress(self) -> None:
        events = []
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)

            rows = run_crawl(
                output_file=None,
                state_dir=None,
                workers=1,
                max_depth=0,
                max_pages_per_site=1,
                fetcher=FakeFetcher(),
                companies=[
                    CompanyInput(
                        keyword="pool heat pump France",
                        title="Acme",
                        website="https://acme.example",
                        domain="acme.example",
                        country="France",
                    )
                ],
                on_domain_done=lambda event: events.append(event),
            )

            state_dirs = list(base.glob(".crawl_state*"))

        self.assertEqual(rows[0]["status"], "success")
        self.assertEqual(state_dirs, [])
        self.assertEqual(events[0]["domain"], "acme.example")
        self.assertEqual(events[0]["status"], "success")

    def test_run_crawl_stops_before_next_domain_when_cancel_requested(self) -> None:
        fetcher = FakeFetcher()

        rows = run_crawl(
            output_file=None,
            state_dir=None,
            workers=1,
            max_depth=0,
            max_pages_per_site=1,
            fetcher=fetcher,
            companies=[
                CompanyInput(
                    keyword="pool heat pump Italy",
                    title="Acme",
                    website="https://acme.example",
                    domain="acme.example",
                ),
                CompanyInput(
                    keyword="pool heat pump Italy",
                    title="Beta",
                    website="https://beta.example",
                    domain="beta.example",
                ),
            ],
            should_cancel=lambda: len(fetcher.urls) >= 1,
        )

        self.assertEqual(fetcher.urls, ["https://acme.example"])
        self.assertEqual([row["domain"] for row in rows], ["acme.example"])

    def test_run_crawl_writes_profile_input_package_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            input_file = base / "company_websites.csv"
            output_file = base / "company_info.csv"
            state_dir = base / "state"
            profile_input_dir = base / "profile_inputs"
            with input_file.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "keyword",
                        "title",
                        "website",
                        "domain",
                        "country",
                        "industry",
                        "matched_keywords",
                        "matched_countries",
                        "matched_industries",
                        "matched_industry_terms",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "keyword": "heat pump installer Germany",
                        "title": "Acme HVAC",
                        "website": "https://acme.example",
                        "domain": "acme.example",
                        "country": "Germany",
                        "industry": "heat_pump",
                        "matched_keywords": "heat pump installer Germany",
                        "matched_countries": "Germany",
                        "matched_industries": "heat_pump",
                        "matched_industry_terms": "heat pump installer",
                    }
                )
            fetcher = FakeFetcher()

            run_crawl(
                input_file=input_file,
                output_file=output_file,
                state_dir=state_dir,
                workers=1,
                max_depth=0,
                max_pages_per_site=1,
                fetcher=fetcher,
                profile_input_dir=profile_input_dir,
                profile_page_char_limit=500,
            )

            package_path = profile_input_dir / "acme.example.json"
            package = json.loads(package_path.read_text(encoding="utf-8"))

        self.assertEqual(package["schema_version"], "1.0")
        self.assertEqual(package["company"]["domain"], "acme.example")
        self.assertEqual(package["company"]["source_keyword"], "heat pump installer Germany")
        self.assertEqual(package["company"]["matched_industries"], "heat_pump")
        self.assertIn("sales@example.com", package["contacts"]["emails"])
        self.assertEqual(package["pages"][0]["category"], "home")
        self.assertIn("Email: sales@example.com", package["pages"][0]["text"])
        self.assertEqual(package["crawl_metadata"]["status"], "success")
        crawl_time = package["crawl_metadata"]["crawl_time"]
        self.assertTrue(crawl_time)
        datetime.fromisoformat(crawl_time)

    def test_run_crawl_honors_profile_page_char_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            input_file = base / "company_websites.csv"
            output_file = base / "company_info.csv"
            state_dir = base / "state"
            profile_input_dir = base / "profile_inputs"
            with input_file.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["keyword", "title", "website", "domain"])
                writer.writeheader()
                writer.writerow(
                    {
                        "keyword": "HVAC Turkey",
                        "title": "Acme",
                        "website": "https://acme.example",
                        "domain": "acme.example",
                    }
                )

            run_crawl(
                input_file=input_file,
                output_file=output_file,
                state_dir=state_dir,
                workers=1,
                max_depth=0,
                max_pages_per_site=1,
                fetcher=FakeFetcher(),
                profile_input_dir=profile_input_dir,
                profile_page_char_limit=10,
            )

            package_path = profile_input_dir / "acme.example.json"
            package = json.loads(package_path.read_text(encoding="utf-8"))

        self.assertLessEqual(len(package["pages"][0]["text"]), 10)

    def test_run_crawl_allows_invalid_profile_page_char_limit_when_export_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            input_file = base / "company_websites.csv"
            output_file = base / "company_info.csv"
            state_dir = base / "state"
            with input_file.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["keyword", "title", "website", "domain"])
                writer.writeheader()
                writer.writerow(
                    {
                        "keyword": "HVAC Turkey",
                        "title": "Acme",
                        "website": "https://acme.example",
                        "domain": "acme.example",
                    }
                )

            rows = run_crawl(
                input_file=input_file,
                output_file=output_file,
                state_dir=state_dir,
                workers=1,
                max_depth=0,
                max_pages_per_site=1,
                fetcher=FakeFetcher(),
                profile_input_dir=None,
                profile_page_char_limit=0,
                emit_profile_package=False,
            )

        self.assertEqual(rows[0]["status"], "success")

    def test_run_crawl_emits_profile_package_payload_without_file_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            input_file = base / "company_websites.csv"
            output_file = base / "company_info.csv"
            state_dir = base / "state"
            with input_file.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["keyword", "title", "website", "domain"])
                writer.writeheader()
                writer.writerow(
                    {
                        "keyword": "pool heat pump France",
                        "title": "Acme",
                        "website": "https://acme.example",
                        "domain": "acme.example",
                    }
                )

            rows = run_crawl(
                input_file=input_file,
                output_file=output_file,
                state_dir=state_dir,
                workers=1,
                max_depth=0,
                max_pages_per_site=1,
                fetcher=FakeFetcher(),
                profile_input_dir=None,
                profile_page_char_limit=500,
            )

            with output_file.open("r", encoding="utf-8-sig", newline="") as file:
                output_rows = list(csv.DictReader(file))

        self.assertEqual(rows[0]["_profile_package"]["company"]["domain"], "acme.example")
        self.assertNotIn("_profile_package", output_rows[0])

    def test_run_crawl_rejects_invalid_profile_page_char_limit_when_export_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            input_file = base / "company_websites.csv"
            output_file = base / "company_info.csv"
            state_dir = base / "state"
            profile_input_dir = base / "profile_inputs"
            with input_file.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["keyword", "title", "website", "domain"])
                writer.writeheader()
                writer.writerow(
                    {
                        "keyword": "HVAC Turkey",
                        "title": "Acme",
                        "website": "https://acme.example",
                        "domain": "acme.example",
                    }
                )

            with self.assertRaisesRegex(ValueError, "profile_page_char_limit must be >= 1"):
                run_crawl(
                    input_file=input_file,
                    output_file=output_file,
                    state_dir=state_dir,
                    workers=1,
                    max_depth=0,
                    max_pages_per_site=1,
                    fetcher=FakeFetcher(),
                    profile_input_dir=profile_input_dir,
                    profile_page_char_limit=0,
                )

    def test_profile_input_export_failure_does_not_fail_crawl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            input_file = base / "company_websites.csv"
            output_file = base / "company_info.csv"
            state_dir = base / "state"
            profile_input_dir = base / "profile_inputs"
            profile_input_dir.write_text("not a directory", encoding="utf-8")
            with input_file.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["keyword", "title", "website", "domain"])
                writer.writeheader()
                writer.writerow(
                    {
                        "keyword": "HVAC Turkey",
                        "title": "Acme",
                        "website": "https://acme.example",
                        "domain": "acme.example",
                    }
                )

            rows = run_crawl(
                input_file=input_file,
                output_file=output_file,
                state_dir=state_dir,
                workers=1,
                max_depth=0,
                max_pages_per_site=1,
                fetcher=FakeFetcher(),
                profile_input_dir=profile_input_dir,
            )
            with output_file.open("r", encoding="utf-8-sig", newline="") as file:
                output_rows = list(csv.DictReader(file))
            state = CrawlState(state_dir)

        self.assertEqual(rows[0]["status"], "success")
        self.assertIn("sales@example.com", rows[0]["emails"])
        self.assertEqual(output_rows[0]["status"], "success")
        self.assertIn("sales@example.com", output_rows[0]["emails"])
        self.assertTrue(state.is_completed("acme.example"))


if __name__ == "__main__":
    unittest.main()
