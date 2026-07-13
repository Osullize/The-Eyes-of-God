from io import BytesIO
from zipfile import ZipFile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from api.app import create_app
from database.models import (
    AIProfileResult,
    CandidateGroup,
    CandidateGroupItem,
    Contact,
    CountrySignal,
    CrawlResult,
    Domain,
    KeywordGroup,
    ProfilePackage,
    QualifiedLead,
    SearchResult,
    TaskItem,
    TaskRun,
)
from database.session import create_all, create_session_factory


class FastApiReadEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
        create_all(self.engine)
        self.session_factory = create_session_factory(self.engine)

        with self.session_factory() as session:
            acme = Domain(
                domain="acme.example",
                website="https://acme.example",
                display_name="Acme Pool Heating",
                description="Pool heating distributor",
                latest_status="success",
            )
            beta = Domain(
                domain="beta.example",
                website="https://beta.example",
                display_name="Beta HVAC",
                description="Installer",
                latest_status="empty",
            )
            session.add_all(
                [
                    acme,
                    beta,
                    SearchResult(domain_record=acme, keyword="pool heat pump", country="France"),
                    CrawlResult(
                        domain_record=acme,
                        keyword="pool heat pump",
                        company_name="Acme Pool Heating",
                        website="https://acme.example",
                        emails="sales@acme.example",
                        status="success",
                        country="France",
                        source_file="company_info_france.csv",
                    ),
                    Contact(domain_record=acme, kind="email", value="sales@acme.example", source="crawl"),
                    ProfilePackage(
                        domain_record=acme,
                        schema_version="1.0",
                        crawl_status="success",
                        page_count=3,
                        content_hash="a" * 64,
                        payload_json={"company": {"domain": "acme.example"}},
                    ),
                    CountrySignal(
                        domain_record=acme,
                        country="France",
                        signal_type="search_country",
                        confidence=0.8,
                        evidence="keyword country",
                        source="company_websites_france.csv",
                    ),
                    QualifiedLead(domain_record=acme, priority="A", status="new", segment="distributor", source="manual"),
                    KeywordGroup(
                        name="France Pool",
                        country="France",
                        country_terms="France",
                        keyword_terms="pool heat pump",
                        notes="fixture",
                        is_active=True,
                    ),
                    TaskRun(task_type="search", name="Search France", status="success", summary_json={"success": 1}),
                ]
            )
            session.flush()
            profile_package = session.query(ProfilePackage).filter_by(domain_record=acme).one()
            session.add(
                AIProfileResult(
                    domain_record=acme,
                    profile_package_id=profile_package.id,
                    model_provider="deepseek",
                    model_name="deepseek-chat",
                    prompt_version="heat_pump_lead_cn_v1",
                    input_hash=profile_package.content_hash,
                    profile_summary="Pool heat pump distributor",
                    business_type="Distributor",
                    market_role="Pool equipment reseller",
                    product_fit="high",
                    customer_priority="A",
                    score_total=86,
                    score_breakdown_json={"product_relevance": 30},
                    evidence_json=["Sells pool heating"],
                    risk_flags_json=[],
                    recommended_action="prioritize_outreach",
                    result_json={
                        "contact_analysis": {
                            "contact_quality": "high",
                            "available_channels": ["email"],
                            "preferred_channel": "email",
                            "recommended_contacts": [],
                            "outreach_strategy": "优先邮件联系。",
                        }
                    },
                    status="success",
                )
            )
            task_run = session.query(TaskRun).filter_by(task_type="search").one()
            search_result = session.query(SearchResult).filter_by(domain_record=acme).one()
            session.add(
                TaskItem(
                    task_run=task_run,
                    item_type="keyword",
                    item_key="pool heat pump France",
                    status="success",
                    attempt_count=1,
                    result_json={"rows": 1},
                )
            )
            session.flush()
            task_item = session.query(TaskItem).filter_by(task_run_id=task_run.id).one()
            candidate_group = CandidateGroup(
                name="France Pool Candidates",
                group_type="search_output",
                source_task_run_id=task_run.id,
                country="France",
                status="active",
                params_json={"limit_keywords": 1},
            )
            session.add(candidate_group)
            session.flush()
            session.add(
                CandidateGroupItem(
                    group_id=candidate_group.id,
                    domain_id=acme.id,
                    search_result_id=search_result.id,
                    source_task_item_id=task_item.id,
                    status="active",
                    rank=1,
                )
            )
            session.commit()

        self.client = TestClient(create_app(session_factory=self.session_factory))

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_database_stats_returns_table_counts(self) -> None:
        response = self.client.get("/database/stats")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "domains": 2,
                "search_results": 1,
                "crawl_results": 1,
                "contacts": 1,
                "profile_packages": 1,
                "country_signals": 1,
            },
        )

    def test_domains_can_be_filtered_by_query_country_and_status(self) -> None:
        response = self.client.get("/domains", params={"q": "acme", "country": "France", "status": "success"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["items"][0]["domain"], "acme.example")
        self.assertEqual(response.json()["items"][0]["display_name"], "Acme Pool Heating")

    def test_domains_returns_total_before_pagination(self) -> None:
        response = self.client.get("/domains", params={"limit": 1})

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["total"], 2)
        self.assertEqual(body["count"], 1)
        self.assertEqual(len(body["items"]), 1)

    def test_domain_detail_includes_contacts_profiles_and_country_signals(self) -> None:
        response = self.client.get("/domains/acme.example")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["domain"]["domain"], "acme.example")
        self.assertEqual(body["contacts"][0]["value"], "sales@acme.example")
        self.assertEqual(body["profile_packages"][0]["content_hash"], "a" * 64)
        self.assertTrue(body["profile_packages"][0]["payload_stored"])
        self.assertEqual(body["country_signals"][0]["country"], "France")

    def test_missing_domain_detail_returns_404(self) -> None:
        response = self.client.get("/domains/missing.example")

        self.assertEqual(response.status_code, 404)

    def test_company_library_stats_returns_stage_counts(self) -> None:
        response = self.client.get("/company-library/stats")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["stage_a_companies"], 1)
        self.assertEqual(response.json()["stage_b_companies"], 1)
        self.assertEqual(response.json()["stage_c_companies"], 1)

    def test_company_library_stage_a_returns_search_candidates(self) -> None:
        response = self.client.get("/company-library/stage-a", params={"country": "France"})

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["domain"]["domain"], "acme.example")
        self.assertEqual(body["items"][0]["latest_search"]["keyword"], "pool heat pump")

    def test_company_library_stage_b_returns_crawled_companies(self) -> None:
        response = self.client.get("/company-library/stage-b", params={"status": "success"})

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["latest_crawl"]["status"], "success")
        self.assertEqual(body["items"][0]["contact_count"], 1)

    def test_company_library_stage_c_returns_qualified_leads(self) -> None:
        response = self.client.get("/company-library/stage-c")

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["qualified_lead"]["priority"], "A")

    def test_raw_table_endpoints_return_paginated_table_rows(self) -> None:
        domains_response = self.client.get("/raw-tables/domains", params={"q": "acme", "status": "success"})
        search_response = self.client.get("/raw-tables/search-results", params={"country": "France", "keyword": "pool"})
        crawl_response = self.client.get("/raw-tables/crawl-results", params={"country": "France", "status": "success"})

        self.assertEqual(domains_response.status_code, 200)
        self.assertEqual(domains_response.json()["total"], 1)
        self.assertEqual(domains_response.json()["items"][0]["display_name"], "Acme Pool Heating")

        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.json()["total"], 1)
        self.assertEqual(search_response.json()["items"][0]["domain"], "acme.example")
        self.assertEqual(search_response.json()["items"][0]["keyword"], "pool heat pump")

        self.assertEqual(crawl_response.status_code, 200)
        self.assertEqual(crawl_response.json()["total"], 1)
        self.assertEqual(crawl_response.json()["items"][0]["domain"], "acme.example")
        self.assertEqual(crawl_response.json()["items"][0]["emails"], "sales@acme.example")

    def test_raw_ai_profile_results_endpoint_returns_ai_outputs(self) -> None:
        response = self.client.get(
            "/raw-tables/ai-profile-results",
            params={"q": "pool", "status": "success", "priority": "A", "model_name": "deepseek-chat", "prompt_version": "cn_v1"},
        )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["domain"], "acme.example")
        self.assertEqual(body["items"][0]["model_name"], "deepseek-chat")
        self.assertEqual(body["items"][0]["customer_priority"], "A")
        self.assertEqual(body["items"][0]["score_total"], 86)
        self.assertEqual(body["items"][0]["contacts"][0]["value"], "sales@acme.example")
        self.assertEqual(body["items"][0]["contact_analysis"]["preferred_channel"], "email")

    def test_keyword_groups_can_be_listed_created_updated_and_deleted(self) -> None:
        list_response = self.client.get("/keyword-groups")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()[0]["name"], "France Pool")

        create_response = self.client.post(
            "/keyword-groups",
            json={
                "name": "UK Pool",
                "country": "United Kingdom",
                "country_terms": "United Kingdom\nUK",
                "keyword_terms": "pool heat pump\npool heating",
                "notes": "new group",
                "is_active": True,
            },
        )
        self.assertEqual(create_response.status_code, 200)
        group_id = create_response.json()["id"]

        update_response = self.client.put(
            f"/keyword-groups/{group_id}",
            json={
                "notes": "updated",
                "is_active": False,
            },
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["notes"], "updated")
        self.assertFalse(update_response.json()["is_active"])

        delete_response = self.client.delete(f"/keyword-groups/{group_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json(), {"deleted": True})

    def test_task_runs_can_be_listed_and_read_with_items(self) -> None:
        list_response = self.client.get("/task-runs")

        self.assertEqual(list_response.status_code, 200)
        list_body = list_response.json()
        self.assertEqual(list_body["total"], 1)
        self.assertEqual(list_body["items"][0]["task_type"], "search")
        self.assertEqual(list_body["items"][0]["item_counts"], {"success": 1})

        detail_response = self.client.get(f"/task-runs/{list_body['items'][0]['id']}")

        self.assertEqual(detail_response.status_code, 200)
        detail_body = detail_response.json()
        self.assertEqual(detail_body["name"], "Search France")
        self.assertEqual(detail_body["items"][0]["item_key"], "pool heat pump France")
        self.assertEqual(detail_body["items"][0]["result_json"], {"rows": 1})

    def test_crawl_task_results_can_be_read_and_exported_as_xlsx(self) -> None:
        with self.session_factory() as session:
            acme = session.query(Domain).filter_by(domain="acme.example").one()
            beta = session.query(Domain).filter_by(domain="beta.example").one()
            crawl_run = TaskRun(task_type="crawl", name="Crawl France Pool", status="success")
            session.add(crawl_run)
            session.flush()
            crawl_run_id = crawl_run.id
            selected_crawl_result = CrawlResult(
                domain_record=acme,
                keyword="pool heat pump France",
                company_name="Acme Pool Heating",
                website="https://acme.example",
                emails="sales@acme.example",
                phones="+33 1 23 45 67",
                possible_address="Paris",
                description="Pool heat pump distributor",
                crawled_pages="3",
                status="success",
                country="France",
                industry="pool heat pump",
                source_file=f"task:crawl:{crawl_run_id}",
            )
            unselected_crawl_result = CrawlResult(
                domain_record=beta,
                keyword="pool heater France",
                company_name="Unselected Export Row",
                website="https://unselected.example",
                emails="skip@unselected.example",
                phones="+33 9 99 99 99",
                possible_address="Lyon",
                description="Should not be in selected export",
                crawled_pages="1",
                status="success",
                country="France",
                industry="pool heater",
                source_file=f"task:crawl:{crawl_run_id}",
            )
            session.add_all([selected_crawl_result, unselected_crawl_result])
            session.flush()
            selected_crawl_result_id = selected_crawl_result.id
            session.commit()

        result_response = self.client.get(f"/task-runs/{crawl_run_id}/results")
        export_response = self.client.get(f"/task-runs/{crawl_run_id}/results/export.xlsx")
        selected_export_response = self.client.get(
            f"/raw-tables/crawl-results/export.xlsx?ids={selected_crawl_result_id}"
        )

        result_body = result_response.json()
        self.assertEqual(result_response.status_code, 200)
        self.assertEqual(result_body["task_run_id"], crawl_run_id)
        self.assertEqual(result_body["result_type"], "crawl")
        self.assertEqual(result_body["total"], 2)
        self.assertTrue(any(item["emails"] == "sales@acme.example" for item in result_body["items"]))

        self.assertEqual(export_response.status_code, 200)
        self.assertEqual(
            export_response.headers["content-type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn(f"crawl-task-{crawl_run_id}-results.xlsx", export_response.headers["content-disposition"])
        with ZipFile(BytesIO(export_response.content)) as workbook:
            sheet_xml = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn("Acme Pool Heating", sheet_xml)
        self.assertIn("sales@acme.example", sheet_xml)

        self.assertEqual(selected_export_response.status_code, 200)
        self.assertIn(
            "crawl-results-selected.xlsx",
            selected_export_response.headers["content-disposition"],
        )
        with ZipFile(BytesIO(selected_export_response.content)) as workbook:
            selected_sheet_xml = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn("Acme Pool Heating", selected_sheet_xml)
        self.assertIn("sales@acme.example", selected_sheet_xml)
        self.assertNotIn("Unselected Export Row", selected_sheet_xml)
        self.assertNotIn("skip@unselected.example", selected_sheet_xml)

    def test_missing_task_run_returns_404(self) -> None:
        response = self.client.get("/task-runs/999")

        self.assertEqual(response.status_code, 404)

    def test_candidate_groups_can_be_listed_and_read_with_items(self) -> None:
        list_response = self.client.get("/candidate-groups")

        self.assertEqual(list_response.status_code, 200)
        list_body = list_response.json()
        self.assertEqual(list_body["total"], 1)
        self.assertEqual(list_body["items"][0]["name"], "France Pool Candidates")
        self.assertEqual(list_body["items"][0]["item_count"], 1)
        self.assertEqual(list_body["items"][0]["crawled_count"], 1)

        detail_response = self.client.get(f"/candidate-groups/{list_body['items'][0]['id']}")

        self.assertEqual(detail_response.status_code, 200)
        detail_body = detail_response.json()
        self.assertEqual(detail_body["items"][0]["domain"]["domain"], "acme.example")
        self.assertEqual(detail_body["items"][0]["search_result"]["keyword"], "pool heat pump")

    def test_profile_source_groups_can_be_listed_and_read(self) -> None:
        with self.session_factory() as session:
            crawl_run = TaskRun(task_type="crawl", name="Crawl France Pool", status="success")
            session.add(crawl_run)
            session.flush()
            profile_package = session.query(ProfilePackage).one()
            profile_package.crawl_task_run_id = crawl_run.id
            package_id = profile_package.id
            crawl_run_id = crawl_run.id
            session.commit()

        list_response = self.client.get("/profile-source-groups")
        detail_response = self.client.get(f"/profile-source-groups/{crawl_run_id}")

        list_body = list_response.json()
        detail_body = detail_response.json()
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_body["total"], 1)
        self.assertEqual(list_body["items"][0]["id"], crawl_run_id)
        self.assertEqual(list_body["items"][0]["name"], "Crawl France Pool")
        self.assertEqual(list_body["items"][0]["profile_package_count"], 1)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_body["profile_package_ids"], [package_id])

    def test_missing_candidate_group_returns_404(self) -> None:
        response = self.client.get("/candidate-groups/999")

        self.assertEqual(response.status_code, 404)

    def test_missing_profile_source_group_returns_404(self) -> None:
        response = self.client.get("/profile-source-groups/999")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
