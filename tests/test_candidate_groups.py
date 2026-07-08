import unittest

from database.candidate_groups import (
    create_candidate_group_from_search_rows,
    get_candidate_group_detail,
    list_candidate_groups,
    select_candidate_group_companies,
)
from database.importers import import_search_rows
from database.models import CandidateGroup, CandidateGroupItem, CrawlResult, Domain
from database.session import create_all, create_engine_from_url, create_session_factory
from database.task_batches import create_task_run


class CandidateGroupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine_from_url("sqlite:///:memory:")
        create_all(self.engine)
        self.Session = create_session_factory(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_search_rows_create_deduped_candidate_group(self) -> None:
        rows = [
            search_row("pool heat pump France", "Acme", "https://acme.example", "acme.example"),
            search_row("pool heating France", "Acme again", "https://acme.example", "acme.example"),
            search_row("pool heat pump France", "Beta", "https://beta.example", "beta.example"),
        ]
        with self.Session() as session:
            task_run = create_task_run(session, task_type="search", name="France search")
            import_search_rows(session, rows, source_name="task:search:1")
            session.flush()

            group = create_candidate_group_from_search_rows(
                session,
                rows=rows,
                source_name="task:search:1",
                name="France pool search",
                source_task_run_id=task_run.id,
                keyword_group_id=None,
                country="France",
                params={"limit_keywords": 2},
            )
            session.commit()

            group_count = session.query(CandidateGroup).count()
            item_count = session.query(CandidateGroupItem).count()

        self.assertIsNotNone(group)
        assert group is not None
        self.assertEqual(group_count, 1)
        self.assertEqual(item_count, 2)
        self.assertEqual(group.name, "France pool search")
        self.assertEqual(group.source_task_run_id, task_run.id)
        self.assertEqual(group.country, "France")
        self.assertEqual(group.params_json, {"limit_keywords": 2})

    def test_candidate_groups_can_be_listed_and_read_with_counts(self) -> None:
        rows = [
            search_row("pool heat pump France", "Acme", "https://acme.example", "acme.example"),
            search_row("pool heat pump France", "Beta", "https://beta.example", "beta.example"),
        ]
        with self.Session() as session:
            import_search_rows(session, rows, source_name="task:search:1")
            session.flush()
            group = create_candidate_group_from_search_rows(
                session,
                rows=rows,
                source_name="task:search:1",
                name="France pool search",
                country="France",
            )
            acme = session.query(Domain).filter(Domain.domain == "acme.example").one()
            session.add(CrawlResult(domain_id=acme.id, status="success", source_file="task:crawl"))
            session.commit()

            listing = list_candidate_groups(session)
            detail = get_candidate_group_detail(session, group.id)

        self.assertEqual(listing["total"], 1)
        item = listing["items"][0]
        self.assertEqual(item["name"], "France pool search")
        self.assertEqual(item["item_count"], 2)
        self.assertEqual(item["crawled_count"], 1)
        self.assertEqual(item["uncrawled_count"], 1)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual([entry["domain"]["domain"] for entry in detail["items"]], ["acme.example", "beta.example"])

    def test_candidate_group_selection_skips_crawled_domains_unless_recrawl_enabled(self) -> None:
        rows = [
            search_row("pool heat pump France", "Acme", "https://acme.example", "acme.example"),
            search_row("pool heat pump France", "Beta", "https://beta.example", "beta.example"),
        ]
        with self.Session() as session:
            import_search_rows(session, rows, source_name="task:search:1")
            session.flush()
            group = create_candidate_group_from_search_rows(
                session,
                rows=rows,
                source_name="task:search:1",
                name="France pool search",
                country="France",
            )
            acme = session.query(Domain).filter(Domain.domain == "acme.example").one()
            session.add(CrawlResult(domain_id=acme.id, status="success", source_file="task:crawl"))
            session.commit()

            uncrawled = select_candidate_group_companies(session, group.id, limit=10, recrawl_existing=False)
            all_candidates = select_candidate_group_companies(session, group.id, limit=10, recrawl_existing=True)

        self.assertEqual([company.domain for company in uncrawled], ["beta.example"])
        self.assertEqual([company.domain for company in all_candidates], ["acme.example", "beta.example"])


def search_row(keyword: str, title: str, website: str, domain: str) -> dict[str, str]:
    return {
        "keyword": keyword,
        "title": title,
        "website": website,
        "domain": domain,
        "source_url": "https://search.example",
        "engine": "duckduckgo",
        "country": "France",
        "country_term": "France",
        "industry": "pool",
        "industry_term": "pool heat pump",
        "matched_keywords": keyword,
        "matched_countries": "France",
        "matched_industries": "pool",
        "matched_industry_terms": "pool heat pump",
    }


if __name__ == "__main__":
    unittest.main()
