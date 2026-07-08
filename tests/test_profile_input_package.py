import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from profile_analysis.input_package import (
    build_profile_input_package,
    safe_package_filename,
    visible_text_from_html,
    write_profile_input_package,
)


class ProfileInputPackageTests(unittest.TestCase):
    def test_visible_text_removes_scripts_styles_and_normalizes_whitespace(self) -> None:
        html = """
            <html>
              <head><style>.hidden { display: none; }</style></head>
              <body>
                <script>window.noisy = true;</script>
                <h1>Heat Pump Services</h1>
                <p>Installation   and maintenance</p>
              </body>
            </html>
        """

        text = visible_text_from_html(html)

        self.assertEqual(text, "Heat Pump Services Installation and maintenance")

    def test_safe_package_filename_normalizes_domain(self) -> None:
        self.assertEqual(safe_package_filename("www.Acme Example.com"), "acme-example.com.json")
        self.assertEqual(safe_package_filename(""), "unknown.json")
        self.assertEqual(safe_package_filename("."), "unknown.json")

    def test_build_profile_input_package_preserves_metadata_contacts_and_priority_pages(self) -> None:
        company = {
            "keyword": "HVAC contractor Germany",
            "title": "Fallback Acme",
            "website": "https://acme.example",
            "domain": "acme.example",
            "country": "Germany",
            "industry": "hvac",
            "matched_keywords": "HVAC contractor Germany; heat pump installer Germany",
            "matched_countries": "Germany",
            "matched_industries": "hvac; heat_pump",
            "matched_industry_terms": "HVAC contractor; heat pump installer",
        }
        profile = SimpleNamespace(
            company_name="Acme HVAC",
            emails=["sales@acme.example"],
            phones=["+49 30 123456"],
            social_links={"linkedin": "https://linkedin.com/company/acme"},
            contacts=[
                SimpleNamespace(
                    name="Jane Smith",
                    title="Sales Manager",
                    email="jane@acme.example",
                )
            ],
        )
        records = [
            SimpleNamespace(
                final_url="https://acme.example/blog",
                category="news",
                html="<html><body><p>Company news</p></body></html>",
            ),
            SimpleNamespace(
                final_url="https://acme.example/services",
                category="service",
                html="""
                    <html>
                      <head><title>Services</title></head>
                      <body><p>Heat pump installation and HVAC project services for commercial buildings.</p></body>
                    </html>
                """,
            ),
        ]

        package = build_profile_input_package(
            company=company,
            profile=profile,
            records=records,
            status="success",
            errors=[],
            crawl_time="2026-06-18T10:00:00+08:00",
            max_pages=1,
            page_char_limit=28,
        )

        self.assertEqual(package["schema_version"], "1.0")
        self.assertEqual(package["company"]["domain"], "acme.example")
        self.assertEqual(package["company"]["company_name"], "Acme HVAC")
        self.assertEqual(package["company"]["source_keyword"], "HVAC contractor Germany")
        self.assertEqual(package["contacts"]["emails"], ["sales@acme.example"])
        self.assertEqual(package["contacts"]["people"][0]["email"], "jane@acme.example")
        self.assertEqual(len(package["pages"]), 1)
        self.assertEqual(package["pages"][0]["category"], "service")
        self.assertEqual(package["pages"][0]["title"], "Services")
        self.assertEqual(package["pages"][0]["text"], "Heat pump installation and")
        self.assertEqual(package["crawl_metadata"]["crawled_pages"], 2)
        self.assertEqual(package["crawl_metadata"]["status"], "success")

    def test_build_profile_input_package_falls_back_to_source_metadata(self) -> None:
        package = build_profile_input_package(
            company={
                "keyword": "solar installer France",
                "country": "France",
                "industry": "solar",
                "matched_keywords": "",
                "matched_countries": "",
                "matched_industries": "",
            },
            profile=SimpleNamespace(contacts=[]),
            records=[],
            status="success",
        )

        self.assertEqual(package["company"]["matched_keywords"], "solar installer France")
        self.assertEqual(package["company"]["matched_countries"], "France")
        self.assertEqual(package["company"]["matched_industries"], "solar")

    def test_build_profile_input_package_defaults_crawl_time_to_iso_timestamp(self) -> None:
        package = build_profile_input_package(
            company={},
            profile=SimpleNamespace(contacts=[]),
            records=[],
            status="success",
            crawl_time=None,
        )

        crawl_time = package["crawl_metadata"]["crawl_time"]
        self.assertTrue(crawl_time)
        datetime.fromisoformat(crawl_time)

    def test_build_profile_input_package_uses_requested_url_when_final_url_is_empty(self) -> None:
        package = build_profile_input_package(
            company={},
            profile=SimpleNamespace(contacts=[]),
            records=[
                SimpleNamespace(
                    final_url="",
                    requested_url="https://acme.example/requested",
                    category="home",
                    html="<html><body><p>Visible page text</p></body></html>",
                )
            ],
            status="success",
        )

        self.assertEqual(package["pages"][0]["url"], "https://acme.example/requested")

    def test_build_profile_input_package_skips_blank_contacts(self) -> None:
        profile = SimpleNamespace(
            contacts=[
                SimpleNamespace(name="", title="", email=""),
                SimpleNamespace(name=None, title=None, email=None),
                SimpleNamespace(name="Jane Smith", title="", email=""),
            ]
        )

        package = build_profile_input_package(company={}, profile=profile, records=[], status="success")

        self.assertEqual(package["contacts"]["people"], [{"name": "Jane Smith", "title": "", "email": ""}])

    def test_write_profile_input_package_uses_domain_filename(self) -> None:
        package = {
            "schema_version": "1.0",
            "company": {"domain": "acme.example"},
            "contacts": {},
            "pages": [],
            "crawl_metadata": {"crawled_pages": 0, "status": "success", "errors": [], "crawl_time": ""},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = write_profile_input_package(package, Path(temp_dir))
            content = path.read_text(encoding="utf-8")

        self.assertEqual(path.name, "acme.example.json")
        self.assertIn('"schema_version": "1.0"', content)


if __name__ == "__main__":
    unittest.main()
