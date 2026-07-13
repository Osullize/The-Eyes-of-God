import unittest
from contextlib import contextmanager

from database.models import (
    AIProfileResult,
    CandidateGroup,
    CompanyProfile,
    Contact,
    CountrySignal,
    CrawlResult,
    Domain,
    LeadScore,
    ProfilePackage,
    QualifiedLead,
    SearchResult,
    TaskRun,
)
from database.queries import (
    get_company_library_stats,
    list_profile_source_groups,
    list_raw_crawl_results,
    list_raw_ai_profile_results,
    list_raw_domains,
    list_raw_search_results,
    list_stage_a_companies,
    list_stage_b_companies,
    list_stage_c_companies,
)
from database.session import create_all, create_engine_from_url, create_session_factory


class DatabaseQueryTests(unittest.TestCase):
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

    def test_company_library_stats_count_distinct_domains_per_stage(self) -> None:
        with self.make_session() as session:
            acme = Domain(domain="acme.example", website="https://acme.example")
            beta = Domain(domain="beta.example", website="https://beta.example")
            gamma = Domain(domain="gamma.example", website="https://gamma.example")
            session.add_all([acme, beta, gamma])
            session.flush()
            session.add_all(
                [
                    SearchResult(domain_record=acme, keyword="pool heat pump France"),
                    SearchResult(domain_record=beta, keyword="HVAC France"),
                    CrawlResult(domain_record=acme, status="success", source_file="task:crawl"),
                    QualifiedLead(domain_record=acme, priority="A", source="manual"),
                ]
            )
            session.commit()

            stats = get_company_library_stats(session)

        self.assertEqual(stats["stage_a_companies"], 2)
        self.assertEqual(stats["stage_b_companies"], 1)
        self.assertEqual(stats["stage_c_companies"], 1)

    def test_list_stage_a_companies_returns_search_candidate_summary(self) -> None:
        with self.make_session() as session:
            domain = Domain(domain="acme.example", website="https://acme.example", display_name="Acme")
            session.add(domain)
            session.flush()
            session.add_all(
                [
                    SearchResult(
                        domain_record=domain,
                        keyword="pool heat pump France",
                        title="Acme Pool Heating",
                        website="https://acme.example",
                        engine="duckduckgo",
                        country="France",
                    ),
                    CountrySignal(
                        domain_record=domain,
                        country="France",
                        signal_type="search_country",
                        confidence=0.4,
                        source="task:search",
                    ),
                ]
            )
            session.commit()

            response = list_stage_a_companies(session, q="acme", country="France")

        self.assertEqual(response["total"], 1)
        self.assertEqual(response["items"][0]["domain"]["domain"], "acme.example")
        self.assertEqual(response["items"][0]["search_result_count"], 1)
        self.assertEqual(response["items"][0]["latest_search"]["keyword"], "pool heat pump France")
        self.assertEqual(response["items"][0]["countries"], ["France"])

    def test_list_stage_b_companies_returns_crawl_profile_summary(self) -> None:
        with self.make_session() as session:
            domain = Domain(domain="acme.example", website="https://acme.example", latest_status="success")
            session.add(domain)
            session.flush()
            session.add_all(
                [
                    CrawlResult(
                        domain_record=domain,
                        company_name="Acme Pool Heating",
                        status="success",
                        description="Pool heat pump distributor",
                        source_file="task:crawl",
                    ),
                    Contact(domain_record=domain, kind="email", value="sales@acme.example", source="task:crawl"),
                    ProfilePackage(
                        domain_record=domain,
                        schema_version="1.0",
                        crawl_status="success",
                        page_count=4,
                        content_hash="a" * 64,
                        payload_json={"company": {"domain": "acme.example"}},
                    ),
                    CountrySignal(
                        domain_record=domain,
                        country="France",
                        signal_type="crawl_country",
                        confidence=0.6,
                        source="task:crawl",
                    ),
                ]
            )
            session.commit()

            response = list_stage_b_companies(session, status="success")

        item = response["items"][0]
        self.assertEqual(response["total"], 1)
        self.assertEqual(item["domain"]["domain"], "acme.example")
        self.assertEqual(item["latest_crawl"]["company_name"], "Acme Pool Heating")
        self.assertEqual(item["contact_count"], 1)
        self.assertEqual(item["profile_package_count"], 1)
        self.assertEqual(item["countries"], ["France"])

    def test_list_stage_c_companies_returns_qualified_lead_summary(self) -> None:
        with self.make_session() as session:
            domain = Domain(domain="acme.example", website="https://acme.example")
            session.add(domain)
            session.flush()
            session.add_all(
                [
                    QualifiedLead(domain_record=domain, priority="A", status="new", segment="distributor", source="manual"),
                    CompanyProfile(
                        domain_record=domain,
                        business_type="Distributor",
                        product_fit="Pool heat pump",
                        market_role="Dealer",
                        summary="Strong fit",
                        source="manual",
                    ),
                    LeadScore(domain_record=domain, score_name="total", score_value=86, reason="Good contactability", source="manual"),
                ]
            )
            session.commit()

            response = list_stage_c_companies(session)

        item = response["items"][0]
        self.assertEqual(response["total"], 1)
        self.assertEqual(item["domain"]["domain"], "acme.example")
        self.assertEqual(item["qualified_lead"]["priority"], "A")
        self.assertEqual(item["company_profile"]["business_type"], "Distributor")
        self.assertEqual(item["scores"][0]["score_name"], "total")

    def test_list_profile_source_groups_returns_crawl_task_groups(self) -> None:
        with self.make_session() as session:
            crawl_run = TaskRun(task_type="crawl", name="Crawl France Pool", status="success")
            candidate_group = CandidateGroup(name="France Pool Candidates", group_type="search_output", country="France")
            acme = Domain(domain="acme.example", website="https://acme.example")
            beta = Domain(domain="beta.example", website="https://beta.example")
            session.add_all([crawl_run, candidate_group, acme, beta])
            session.flush()
            package_one = ProfilePackage(
                domain_record=acme,
                candidate_group_id=candidate_group.id,
                crawl_task_run_id=crawl_run.id,
                schema_version="1.0",
                crawl_status="success",
                page_count=3,
                content_hash="b" * 64,
                payload_json={"company": {"domain": "acme.example"}},
            )
            package_two = ProfilePackage(
                domain_record=beta,
                candidate_group_id=candidate_group.id,
                crawl_task_run_id=crawl_run.id,
                schema_version="1.0",
                crawl_status="success",
                page_count=4,
                content_hash="c" * 64,
                payload_json={"company": {"domain": "beta.example"}},
            )
            session.add_all([package_one, package_two])
            session.flush()
            session.add(
                AIProfileResult(
                    domain_record=acme,
                    profile_package_id=package_one.id,
                    model_provider="deepseek",
                    model_name="deepseek-v4-pro",
                    prompt_version="heat_pump_lead_cn_v1",
                    input_hash=package_one.content_hash,
                    customer_priority="A",
                    score_total=86,
                    status="success",
                )
            )
            session.commit()

            response = list_profile_source_groups(session)

        item = response["items"][0]
        self.assertEqual(response["total"], 1)
        self.assertEqual(item["id"], crawl_run.id)
        self.assertEqual(item["name"], "Crawl France Pool")
        self.assertEqual(item["candidate_group_id"], candidate_group.id)
        self.assertEqual(item["candidate_group_name"], "France Pool Candidates")
        self.assertEqual(item["profile_package_count"], 2)
        self.assertEqual(item["ai_profile_count"], 1)
        self.assertEqual(item["pending_profile_count"], 1)
        self.assertEqual(item["profile_package_ids"], [package_one.id, package_two.id])

    def test_raw_table_queries_return_full_rows_with_filters(self) -> None:
        with self.make_session() as session:
            acme = Domain(
                domain="acme.example",
                website="https://acme.example",
                display_name="Acme Pool",
                description="Pool heat pump distributor",
                latest_status="success",
            )
            beta = Domain(
                domain="beta.example",
                website="https://beta.example",
                display_name="Beta HVAC",
                description="Installer",
                latest_status="empty",
            )
            session.add_all([acme, beta])
            session.flush()
            session.add_all(
                [
                    SearchResult(
                        domain_record=acme,
                        keyword="pool heat pump",
                        title="Acme Pool Heating",
                        website="https://acme.example",
                        source_url="https://search.example/result",
                        engine="bing",
                        country="France",
                        country_term="France",
                        industry="Pool heating",
                        industry_term="pool",
                        matched_keywords="pool heat pump",
                        matched_countries="France",
                        matched_industries="Pool heating",
                        matched_industry_terms="pool",
                        source_file="task:search",
                    ),
                    CrawlResult(
                        domain_record=acme,
                        keyword="pool heat pump",
                        company_name="Acme Pool Heating",
                        website="https://acme.example",
                        emails="sales@acme.example",
                        phones="+33123456789",
                        possible_address="Paris, France",
                        description="Pool heat pump distributor",
                        crawled_pages="https://acme.example\nhttps://acme.example/contact",
                        status="success",
                        social_links="https://linkedin.com/company/acme",
                        contacts="sales@acme.example",
                        page_categories="home,contact",
                        country="France",
                        industry="Pool heating",
                        matched_keywords="pool heat pump",
                        matched_countries="France",
                        matched_industries="Pool heating",
                        matched_industry_terms="pool",
                        source_file="task:crawl",
                    ),
                ]
            )
            session.commit()

            domains = list_raw_domains(session, q="pool", status="success")
            search_results = list_raw_search_results(session, q="acme", country="France", engine="bing", keyword="pool")
            crawl_results = list_raw_crawl_results(session, q="Paris", country="France", status="success", keyword="pool")

        self.assertEqual(domains["total"], 1)
        self.assertEqual(domains["items"][0]["domain"], "acme.example")
        self.assertEqual(domains["items"][0]["latest_status"], "success")

        self.assertEqual(search_results["total"], 1)
        self.assertEqual(search_results["items"][0]["domain"], "acme.example")
        self.assertEqual(search_results["items"][0]["domain_id"], domains["items"][0]["id"])
        self.assertEqual(search_results["items"][0]["country_term"], "France")
        self.assertEqual(search_results["items"][0]["matched_industry_terms"], "pool")

        self.assertEqual(crawl_results["total"], 1)
        self.assertEqual(crawl_results["items"][0]["company_name"], "Acme Pool Heating")
        self.assertEqual(crawl_results["items"][0]["emails"], "sales@acme.example")
        self.assertEqual(crawl_results["items"][0]["page_categories"], "home,contact")

    def test_list_raw_ai_profile_results_returns_full_rows_with_filters(self) -> None:
        with self.make_session() as session:
            domain = Domain(domain="ai.example", website="https://ai.example")
            session.add(domain)
            session.flush()
            session.add(
                CountrySignal(
                    domain_id=domain.id,
                    country="Italy",
                    signal_type="search_country",
                    source="search",
                    evidence="Italy pool keyword",
                )
            )
            package = ProfilePackage(
                domain_record=domain,
                schema_version="1.0",
                crawl_status="success",
                page_count=3,
                payload_json={"company": {"domain": "ai.example"}},
                content_hash="d" * 64,
            )
            session.add(package)
            session.flush()
            session.add(
                AIProfileResult(
                    domain_record=domain,
                    profile_package_id=package.id,
                    model_provider="deepseek",
                    model_name="deepseek-chat",
                    prompt_version="heat_pump_lead_cn_v1",
                    input_hash=package.content_hash,
                    company_name="Acme AI Heating",
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
            session.commit()

            response = list_raw_ai_profile_results(
                session,
                q="Acme AI",
                status="success",
                priority="A",
                model_name="deepseek-chat",
                prompt_version="cn_v1",
            )

        self.assertEqual(response["total"], 1)
        self.assertEqual(response["items"][0]["domain"], "ai.example")
        self.assertEqual(response["items"][0]["profile_package_id"], package.id)
        self.assertEqual(response["items"][0]["company_name"], "Acme AI Heating")
        self.assertEqual(response["items"][0]["country"], "Italy")
        self.assertEqual(response["items"][0]["model_name"], "deepseek-chat")
        self.assertEqual(response["items"][0]["customer_priority"], "A")
        self.assertEqual(response["items"][0]["score_total"], 86)
        self.assertIn("product_relevance", response["items"][0]["score_breakdown_json"])
        self.assertEqual(response["items"][0]["contact_analysis"]["preferred_channel"], "email")

    def test_list_raw_ai_profile_results_allows_large_directory_pages(self) -> None:
        with self.make_session() as session:
            domain = Domain(domain="large-directory.example", website="https://large-directory.example")
            session.add(domain)
            session.flush()
            package = ProfilePackage(
                domain_record=domain,
                schema_version="1.0",
                crawl_status="success",
                page_count=1,
                payload_json={"company": {"domain": "large-directory.example"}},
                content_hash="e" * 64,
            )
            session.add(package)
            session.flush()
            session.add(
                AIProfileResult(
                    domain_record=domain,
                    profile_package_id=package.id,
                    model_provider="deepseek",
                    model_name="deepseek-chat",
                    prompt_version="heat_pump_lead_cn_v1",
                    input_hash=package.content_hash,
                    company_name="Large Directory Heating",
                    customer_priority="B",
                    score_total=70,
                    status="success",
                )
            )
            session.commit()

            response = list_raw_ai_profile_results(session, limit=500)

        self.assertEqual(response["limit"], 500)
        self.assertEqual(response["total"], 1)


if __name__ == "__main__":
    unittest.main()
