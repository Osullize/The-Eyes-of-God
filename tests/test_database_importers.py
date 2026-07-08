import csv
import json
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from database.importers import import_crawl_csv, import_crawl_rows, import_profile_dir, import_search_csv, import_search_rows
from database.models import CandidateGroup, Contact, CountrySignal, CrawlResult, Domain, ProfilePackage, SearchResult, TaskRun
from database.session import create_all, create_engine_from_url, create_session_factory


SEARCH_FIELDS = [
    "keyword",
    "title",
    "website",
    "domain",
    "source_url",
    "engine",
    "country",
    "country_term",
    "industry",
    "industry_term",
    "matched_keywords",
    "matched_countries",
    "matched_industries",
    "matched_industry_terms",
]


CRAWL_FIELDS = [
    "keyword",
    "company_name",
    "website",
    "domain",
    "emails",
    "phones",
    "possible_address",
    "description",
    "crawled_pages",
    "status",
    "error",
    "social_links",
    "contacts",
    "page_categories",
    "country",
    "industry",
    "matched_keywords",
    "matched_countries",
    "matched_industries",
    "matched_industry_terms",
]


class DatabaseImporterTests(unittest.TestCase):
    @contextmanager
    def make_session(self):
        engine = create_engine_from_url("sqlite:///:memory:")
        create_all(engine)
        Session = create_session_factory(engine)
        session = Session()
        try:
            yield session
        finally:
            session.close()
            engine.dispose()

    def test_import_search_csv_dedupes_domains_and_preserves_search_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "company_websites.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=SEARCH_FIELDS)
                writer.writeheader()
                writer.writerow(
                    {
                        "keyword": "pool heat pump France",
                        "title": "Acme France",
                        "website": "https://www.acme.example/fr",
                        "domain": "acme.example",
                        "source_url": "https://search.local/fr",
                        "engine": "duckduckgo",
                        "country": "France",
                        "country_term": "France",
                        "industry": "pool_heat_pump",
                        "industry_term": "pool heat pump",
                        "matched_keywords": "pool heat pump France",
                        "matched_countries": "France",
                        "matched_industries": "pool_heat_pump",
                        "matched_industry_terms": "pool heat pump",
                    }
                )
                writer.writerow(
                    {
                        "keyword": "heat pump United Kingdom",
                        "title": "Acme UK",
                        "website": "https://acme.example/uk",
                        "domain": "acme.example",
                        "source_url": "https://search.local/uk",
                        "engine": "bing",
                        "country": "United Kingdom",
                        "country_term": "UK",
                        "industry": "heat_pump",
                        "industry_term": "heat pump",
                        "matched_keywords": "heat pump United Kingdom",
                        "matched_countries": "United Kingdom",
                        "matched_industries": "heat_pump",
                        "matched_industry_terms": "heat pump",
                    }
                )

            with self.make_session() as session:
                summary = import_search_csv(session, path)
                session.commit()

                domains = session.query(Domain).all()
                search_rows = session.query(SearchResult).order_by(SearchResult.keyword).all()
                signals = session.query(CountrySignal).order_by(CountrySignal.country).all()

        self.assertEqual(summary.domains_created, 1)
        self.assertEqual(summary.search_results_created, 2)
        self.assertEqual(len(domains), 1)
        self.assertEqual(domains[0].domain, "acme.example")
        self.assertEqual(len(search_rows), 2)
        self.assertEqual({row.country for row in search_rows}, {"France", "United Kingdom"})
        self.assertEqual({signal.country for signal in signals}, {"France", "United Kingdom"})
        self.assertEqual({signal.signal_type for signal in signals}, {"search_country"})

    def test_import_search_rows_persists_task_output_without_csv_file(self) -> None:
        rows = [
            {
                "keyword": "pool heat pump France",
                "title": "Acme France",
                "website": "https://www.acme.example/fr",
                "domain": "acme.example",
                "source_url": "https://search.local/fr",
                "engine": "duckduckgo",
                "country": "France",
                "country_term": "France",
                "industry": "pool_heat_pump",
                "industry_term": "pool heat pump",
                "matched_keywords": "pool heat pump France",
                "matched_countries": "France",
                "matched_industries": "pool_heat_pump",
                "matched_industry_terms": "pool heat pump",
            }
        ]

        with self.make_session() as session:
            summary = import_search_rows(session, rows, source_name="task:search:france")
            session.commit()

            domain = session.query(Domain).one()
            search_result = session.query(SearchResult).one()
            signal = session.query(CountrySignal).filter(CountrySignal.signal_type == "search_country").one()

        self.assertEqual(summary.domains_created, 1)
        self.assertEqual(summary.search_results_created, 1)
        self.assertEqual(domain.domain, "acme.example")
        self.assertEqual(search_result.source_file, "task:search:france")
        self.assertEqual(signal.source, "task:search:france")

    def test_import_crawl_csv_updates_domain_summary_and_contacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "company_info.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=CRAWL_FIELDS)
                writer.writeheader()
                writer.writerow(
                    {
                        "keyword": "pool heat pump France",
                        "company_name": "Acme Pool Heating",
                        "website": "https://acme.example",
                        "domain": "acme.example",
                        "emails": "sales@acme.example; info@acme.example",
                        "phones": "+33 1 23 45 67 89; +33 6 12 34 56 78",
                        "possible_address": "12 Rue Example, Paris",
                        "description": "Distributor of swimming pool heat pumps.",
                        "crawled_pages": "https://acme.example; https://acme.example/contact",
                        "status": "success",
                        "error": "",
                        "social_links": "linkedin:https://linkedin.com/company/acme; facebook:https://facebook.com/acme",
                        "contacts": "",
                        "page_categories": "home:https://acme.example; contact:https://acme.example/contact",
                        "country": "France",
                        "industry": "pool_heat_pump",
                        "matched_keywords": "pool heat pump France",
                        "matched_countries": "France",
                        "matched_industries": "pool_heat_pump",
                        "matched_industry_terms": "pool heat pump",
                    }
                )

            with self.make_session() as session:
                summary = import_crawl_csv(session, path)
                session.commit()

                domain = session.query(Domain).one()
                crawl_result = session.query(CrawlResult).one()
                contacts = session.query(Contact).order_by(Contact.kind, Contact.value).all()
                signals = session.query(CountrySignal).all()

        self.assertEqual(summary.domains_created, 1)
        self.assertEqual(summary.crawl_results_created, 1)
        self.assertEqual(summary.contacts_created, 6)
        self.assertEqual(domain.display_name, "Acme Pool Heating")
        self.assertEqual(domain.latest_status, "success")
        self.assertEqual(domain.description, "Distributor of swimming pool heat pumps.")
        self.assertEqual(crawl_result.status, "success")
        self.assertEqual({contact.kind for contact in contacts}, {"email", "phone", "social"})
        self.assertIn("sales@acme.example", {contact.value for contact in contacts})
        self.assertIn("https://linkedin.com/company/acme", {contact.value for contact in contacts})
        self.assertEqual({signal.country for signal in signals}, {"France"})
        self.assertEqual(signals[0].signal_type, "crawl_country")

    def test_import_crawl_rows_persists_task_output_without_csv_file(self) -> None:
        profile_package = {
            "schema_version": "1.0",
            "company": {
                "domain": "acme.example",
                "website": "https://acme.example",
                "company_name": "Acme Pool Heating",
                "country": "France",
            },
            "contacts": {"emails": ["sales@acme.example"], "phones": [], "social_links": {}, "people": []},
            "pages": [{"url": "https://acme.example", "category": "home", "title": "Home", "text": "Pool heat pumps"}],
            "crawl_metadata": {"status": "success", "crawl_time": "2026-06-24T10:00:00+00:00"},
        }
        rows = [
            {
                "keyword": "pool heat pump France",
                "company_name": "Acme Pool Heating",
                "website": "https://acme.example",
                "domain": "acme.example",
                "emails": "sales@acme.example",
                "phones": "+33 1 23 45 67 89",
                "possible_address": "12 Rue Example, Paris",
                "description": "Distributor of swimming pool heat pumps.",
                "crawled_pages": "https://acme.example; https://acme.example/contact",
                "status": "success",
                "error": "",
                "social_links": "linkedin:https://linkedin.com/company/acme",
                "contacts": "",
                "page_categories": "home:https://acme.example; contact:https://acme.example/contact",
                "country": "France",
                "industry": "pool_heat_pump",
                "matched_keywords": "pool heat pump France",
                "matched_countries": "France",
                "matched_industries": "pool_heat_pump",
                "matched_industry_terms": "pool heat pump",
                "_profile_package": profile_package,
            }
        ]

        with self.make_session() as session:
            summary = import_crawl_rows(session, rows, source_name="task:crawl:france")
            session.commit()

            domain = session.query(Domain).one()
            crawl_result = session.query(CrawlResult).one()
            contacts = session.query(Contact).order_by(Contact.kind, Contact.value).all()
            signal = session.query(CountrySignal).filter(CountrySignal.signal_type == "crawl_country").one()
            persisted_profile = session.query(ProfilePackage).one()

        self.assertEqual(summary.domains_created, 1)
        self.assertEqual(summary.crawl_results_created, 1)
        self.assertEqual(summary.profile_packages_created, 1)
        self.assertEqual(summary.contacts_created, 4)
        self.assertEqual(domain.latest_status, "success")
        self.assertEqual(crawl_result.source_file, "task:crawl:france")
        self.assertEqual(persisted_profile.payload_json["company"]["domain"], "acme.example")
        self.assertEqual(persisted_profile.crawl_result_id, crawl_result.id)
        self.assertEqual({contact.kind for contact in contacts}, {"email", "phone", "social"})
        self.assertEqual(signal.source, "task:crawl:france")

    def test_import_crawl_rows_attaches_generated_profile_to_source_group(self) -> None:
        profile_package = {
            "schema_version": "1.0",
            "company": {
                "domain": "acme.example",
                "website": "https://acme.example",
                "company_name": "Acme Pool Heating",
                "country": "Italy",
            },
            "contacts": {},
            "pages": [{"url": "https://acme.example", "category": "home", "title": "Home", "text": "Heat pumps"}],
            "crawl_metadata": {"status": "success", "crawl_time": "2026-06-24T10:00:00+00:00"},
        }
        rows = [
            {
                "keyword": "pompa di calore piscina Italia",
                "company_name": "Acme Pool Heating",
                "website": "https://acme.example",
                "domain": "acme.example",
                "emails": "",
                "phones": "",
                "possible_address": "",
                "description": "Italian pool heat pump distributor.",
                "crawled_pages": "https://acme.example",
                "status": "success",
                "error": "",
                "social_links": "",
                "contacts": "",
                "page_categories": "home:https://acme.example",
                "country": "Italy",
                "industry": "pool_heat_pump",
                "matched_keywords": "pompa di calore piscina Italia",
                "matched_countries": "Italy",
                "matched_industries": "pool_heat_pump",
                "matched_industry_terms": "pompa di calore piscina",
                "_profile_package": profile_package,
            }
        ]

        with self.make_session() as session:
            task_run = TaskRun(task_type="crawl", name="Crawl task", status="success")
            candidate_group = CandidateGroup(name="Italy pool candidates", group_type="search_output", country="Italy")
            session.add_all([task_run, candidate_group])
            session.flush()

            summary = import_crawl_rows(
                session,
                rows,
                source_name="task:crawl:42",
                candidate_group_id=candidate_group.id,
                crawl_task_run_id=task_run.id,
            )
            session.commit()

            crawl_result = session.query(CrawlResult).one()
            persisted_profile = session.query(ProfilePackage).one()

        self.assertEqual(summary.profile_packages_created, 1)
        self.assertEqual(persisted_profile.crawl_result_id, crawl_result.id)
        self.assertEqual(persisted_profile.candidate_group_id, candidate_group.id)
        self.assertEqual(persisted_profile.crawl_task_run_id, task_run.id)

    def test_import_profile_dir_upserts_packages_contacts_and_country_signals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir) / "profile_inputs"
            profile_dir.mkdir()
            package_path = profile_dir / "acme.example.json"
            package_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "company": {
                            "domain": "acme.example",
                            "website": "https://acme.example",
                            "company_name": "Acme Pool Heating",
                            "country": "France",
                            "industry": "pool_heat_pump",
                        },
                        "contacts": {
                            "emails": ["sales@acme.example"],
                            "phones": ["+33 1 23 45 67 89"],
                            "social_links": {"linkedin": "https://linkedin.com/company/acme"},
                            "people": [
                                {
                                    "name": "Jane Martin",
                                    "title": "Sales Manager",
                                    "email": "jane@acme.example",
                                }
                            ],
                        },
                        "pages": [
                            {"url": "https://acme.example", "category": "home", "title": "Home", "text": "Home"},
                            {
                                "url": "https://acme.example/contact",
                                "category": "contact",
                                "title": "Contact",
                                "text": "Contact",
                            },
                        ],
                        "crawl_metadata": {
                            "crawled_pages": 2,
                            "status": "success",
                            "errors": [],
                            "crawl_time": "2026-06-24T10:00:00+00:00",
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.make_session() as session:
                summary = import_profile_dir(session, profile_dir)
                session.commit()

                domain = session.query(Domain).one()
                profile_package = session.query(ProfilePackage).one()
                contacts = session.query(Contact).order_by(Contact.kind, Contact.value).all()
                signals = session.query(CountrySignal).all()

        self.assertEqual(summary.domains_created, 1)
        self.assertEqual(summary.profile_packages_created, 1)
        self.assertEqual(summary.contacts_created, 4)
        self.assertEqual(domain.domain, "acme.example")
        self.assertEqual(domain.display_name, "Acme Pool Heating")
        self.assertEqual(profile_package.schema_version, "1.0")
        self.assertEqual(profile_package.page_count, 2)
        self.assertEqual(profile_package.crawl_status, "success")
        self.assertEqual(profile_package.payload_json["company"]["domain"], "acme.example")
        self.assertEqual(profile_package.payload_json["pages"][1]["category"], "contact")
        self.assertEqual(len(profile_package.content_hash), 64)
        self.assertIn("jane@acme.example", {contact.value for contact in contacts})
        self.assertIn("Jane Martin | Sales Manager", {contact.label for contact in contacts})
        self.assertEqual({signal.country for signal in signals}, {"France"})
        self.assertEqual(signals[0].signal_type, "profile_country")

    def test_import_profile_dir_dedupes_same_payload_by_content_hash_not_path(self) -> None:
        package = {
            "schema_version": "1.0",
            "company": {
                "domain": "acme.example",
                "website": "https://acme.example",
                "company_name": "Acme Pool Heating",
            },
            "contacts": {},
            "pages": [{"url": "https://acme.example", "category": "home", "title": "Home", "text": "Home"}],
            "crawl_metadata": {"status": "success"},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            first_dir = Path(temp_dir) / "relative_style"
            second_dir = Path(temp_dir) / "absolute_style"
            first_dir.mkdir()
            second_dir.mkdir()
            (first_dir / "acme.example.json").write_text(json.dumps(package), encoding="utf-8")
            (second_dir / "acme.example.json").write_text(json.dumps(package, indent=2), encoding="utf-8")

            with self.make_session() as session:
                first_summary = import_profile_dir(session, first_dir)
                second_summary = import_profile_dir(session, second_dir)
                session.commit()

                profile_packages = session.query(ProfilePackage).all()

        self.assertEqual(first_summary.profile_packages_created, 1)
        self.assertEqual(second_summary.profile_packages_updated, 1)
        self.assertEqual(len(profile_packages), 1)
        self.assertEqual(profile_packages[0].payload_json["company"]["domain"], "acme.example")

    def test_import_profile_dir_can_attach_candidate_group_and_crawl_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir) / "profile_inputs"
            profile_dir.mkdir()
            (profile_dir / "acme.example.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "company": {
                            "domain": "acme.example",
                            "website": "https://acme.example",
                            "company_name": "Acme Pool Heating",
                        },
                        "contacts": {},
                        "pages": [],
                        "crawl_metadata": {"status": "success"},
                    }
                ),
                encoding="utf-8",
            )

            with self.make_session() as session:
                task_run = TaskRun(task_type="crawl", name="Crawl task", status="success")
                candidate_group = CandidateGroup(name="Italy pool candidates", group_type="search_output", country="Italy")
                session.add_all([task_run, candidate_group])
                session.flush()

                summary = import_profile_dir(
                    session,
                    profile_dir,
                    candidate_group_id=candidate_group.id,
                    crawl_task_run_id=task_run.id,
                )
                session.commit()

                profile_package = session.query(ProfilePackage).one()

        self.assertEqual(summary.profile_packages_created, 1)
        self.assertEqual(profile_package.candidate_group_id, candidate_group.id)
        self.assertEqual(profile_package.crawl_task_run_id, task_run.id)

    def test_import_profile_dir_skips_json_without_company_domain_or_website(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir) / "profile_inputs"
            profile_dir.mkdir()
            (profile_dir / "heat_pump_lead_analysis.json").write_text(
                json.dumps(
                    {
                        "summary": {"total": 10},
                        "items": [{"domain": "not-a-profile-package.example"}],
                    }
                ),
                encoding="utf-8",
            )

            with self.make_session() as session:
                summary = import_profile_dir(session, profile_dir)
                session.commit()

                domain_count = session.query(Domain).count()
                profile_count = session.query(ProfilePackage).count()

        self.assertEqual(summary.files_scanned, 1)
        self.assertEqual(summary.domains_created, 0)
        self.assertEqual(summary.profile_packages_created, 0)
        self.assertEqual(domain_count, 0)
        self.assertEqual(profile_count, 0)


if __name__ == "__main__":
    unittest.main()
