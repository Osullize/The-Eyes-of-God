import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database.candidate_groups import create_candidate_group_from_search_rows
from database.importers import import_search_rows
from database.models import (
    AIProfileResult,
    CandidateGroup,
    CandidateGroupItem,
    CompanyProfile,
    Contact,
    CountrySignal,
    CrawlResult,
    Domain,
    KeywordGroup,
    LeadScore,
    ProfilePackage,
    QualifiedLead,
    SearchResult,
    TaskItem,
    TaskRun,
)
from database.session import create_all, create_engine_from_url, create_session_factory
from tasks.handlers import (
    run_ai_profile_task,
    run_crawl_task,
    run_import_existing_data_task,
    run_search_task,
)


class TaskHandlerTests(unittest.TestCase):
    def test_run_ai_profile_task_analyzes_selected_profile_packages(self) -> None:
        calls = []

        def fake_analyzer(payload, options):
            calls.append({"payload": payload, "options": options})
            return {
                "company_name": "Acme Pool Heating",
                "profile_summary": "Pool heat pump distributor",
                "business_type": "distributor",
                "market_role": "pool equipment reseller",
                "product_fit": "high",
                "customer_priority": "A",
                "score_total": 86,
                "score_breakdown": {"product_relevance": 30},
                "contact_analysis": {
                    "contact_quality": "high",
                    "available_channels": ["email", "phone", "person"],
                    "preferred_channel": "person",
                    "recommended_contacts": [
                        {
                            "type": "person",
                            "value": "buyer@acme.example",
                            "label": "Jane Buyer | Purchasing Manager",
                            "reason": "优先联系采购负责人",
                        }
                    ],
                    "outreach_strategy": "先向采购负责人发送产品合作邮件，再电话跟进。",
                },
                "evidence": ["Sells swimming pool heating products"],
                "risk_flags": [],
                "recommended_action": "prioritize_outreach",
                "_raw_response": {"id": "fake-response"},
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                domain = Domain(domain="acme.example", website="https://acme.example")
                session.add(domain)
                session.flush()
                package = ProfilePackage(
                    domain_record=domain,
                    schema_version="1.0",
                    crawl_status="success",
                    page_count=2,
                    payload_json={
                        "company": {"domain": "acme.example", "company_name": "Acme Pool Heating"},
                        "contacts": {"emails": ["legacy@acme.example"]},
                        "pages": [{"text": "Swimming pool heating and heat pumps"}],
                    },
                    content_hash="a" * 64,
                )
                session.add(package)
                session.flush()
                session.add_all(
                    [
                        Contact(
                            domain_record=domain,
                            kind="email",
                            value="sales@acme.example",
                            label="销售邮箱",
                            source="crawl_csv",
                        ),
                        Contact(
                            domain_record=domain,
                            kind="email",
                            value="sales@acme.example",
                            source="profile_json",
                        ),
                        Contact(
                            domain_record=domain,
                            kind="phone",
                            value="+39 02 1234 5678",
                            source="profile_json",
                        ),
                        Contact(
                            domain_record=domain,
                            kind="person",
                            value="buyer@acme.example",
                            label="Jane Buyer | Purchasing Manager",
                            source="profile_json",
                        ),
                    ]
                )
                session.commit()
                package_id = package.id
            engine.dispose()

            summary = run_ai_profile_task(
                {
                    "database_url": database_url,
                    "profile_package_ids": [package_id],
                    "model_provider": "deepseek",
                    "model_name": "deepseek-chat",
                    "api_base_url": "https://api.deepseek.com",
                    "api_key": "sk-task-secret",
                    "persist_to_database": True,
                },
                analyzer=fake_analyzer,
            )

            engine = create_engine_from_url(database_url)
            Session = create_session_factory(engine)
            with Session() as session:
                task_run = session.query(TaskRun).one()
                task_item = session.query(TaskItem).one()
                result = session.query(AIProfileResult).one()
                qualified_lead = session.query(QualifiedLead).one()
                company_profile = session.query(CompanyProfile).one()
                scores = {score.score_name: score for score in session.query(LeadScore).all()}
            engine.dispose()

        self.assertEqual(summary["profile_packages"], 1)
        self.assertEqual(summary["results_created"], 1)
        self.assertEqual(summary["task_run_id"], task_run.id)
        self.assertEqual(task_run.task_type, "ai_profile")
        self.assertEqual(task_run.status, "success")
        self.assertEqual(task_item.item_type, "profile_package")
        self.assertEqual(task_item.item_key, str(package_id))
        self.assertEqual(task_item.status, "success")
        self.assertEqual(task_item.result_json["promoted_to_qualified_lead"], True)
        self.assertEqual(result.profile_package_id, package_id)
        self.assertEqual(result.model_provider, "deepseek")
        self.assertEqual(result.model_name, "deepseek-chat")
        self.assertEqual(result.prompt_version, "heat_pump_lead_cn_v2")
        self.assertEqual(result.result_json["contact_analysis"]["preferred_channel"], "person")
        self.assertEqual(len(result.input_hash), 64)
        self.assertNotEqual(result.input_hash, "a" * 64)
        self.assertEqual(result.customer_priority, "A")
        self.assertEqual(result.score_total, 86)
        self.assertEqual(result.raw_response_json["id"], "fake-response")
        self.assertEqual(qualified_lead.domain_id, result.domain_id)
        self.assertEqual(qualified_lead.priority, "A")
        self.assertEqual(qualified_lead.status, "new")
        self.assertEqual(qualified_lead.segment, "pool equipment reseller")
        self.assertEqual(company_profile.domain_id, result.domain_id)
        self.assertEqual(company_profile.business_type, "distributor")
        self.assertEqual(company_profile.product_fit, "high")
        self.assertEqual(company_profile.market_role, "pool equipment reseller")
        self.assertEqual(company_profile.summary, "Pool heat pump distributor")
        self.assertIn("Sells swimming pool heating products", company_profile.evidence)
        self.assertEqual(scores["total"].score_value, 86)
        self.assertEqual(scores["product_relevance"].score_value, 30)
        self.assertEqual(calls[0]["payload"]["company"]["domain"], "acme.example")
        self.assertEqual(calls[0]["payload"]["contacts"]["emails"], ["legacy@acme.example"])
        normalized_contacts = calls[0]["payload"]["contacts"]["normalized_records"]
        self.assertEqual(len(normalized_contacts), 3)
        self.assertEqual(
            {(contact["kind"], contact["value"]) for contact in normalized_contacts},
            {
                ("email", "sales@acme.example"),
                ("phone", "+39 02 1234 5678"),
                ("person", "buyer@acme.example"),
            },
        )
        self.assertTrue(all("source" not in contact for contact in normalized_contacts))
        self.assertEqual(calls[0]["options"]["api_base_url"], "https://api.deepseek.com")
        self.assertNotIn("api_key", task_run.params_json)

    def test_run_ai_profile_task_passes_requested_model_to_analyzer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                domain = Domain(domain="model.example", website="https://model.example")
                session.add(domain)
                session.flush()
                package = ProfilePackage(
                    domain_record=domain,
                    schema_version="1.0",
                    crawl_status="success",
                    page_count=1,
                    payload_json={"company": {"domain": "model.example"}},
                    content_hash="b" * 64,
                )
                session.add(package)
                session.commit()
                package_id = package.id
            engine.dispose()

            seen_options = []

            def fake_analyzer(payload, options):
                seen_options.append(options)
                return {
                    "profile_summary": "",
                    "business_type": "",
                    "market_role": "",
                    "product_fit": "",
                    "customer_priority": "B",
                    "score_total": 70,
                    "score_breakdown": {},
                    "evidence": [],
                    "risk_flags": [],
                    "recommended_action": "",
                }

            run_ai_profile_task(
                {
                    "database_url": database_url,
                    "profile_package_ids": [package_id],
                    "model_provider": "deepseek",
                    "model_name": "deepseek-reasoner",
                    "api_base_url": "https://api.deepseek.com",
                    "api_key": "sk-task-secret",
                },
                analyzer=fake_analyzer,
            )

        self.assertEqual(seen_options[0]["model_name"], "deepseek-reasoner")
        self.assertEqual(seen_options[0]["prompt_version"], "heat_pump_lead_cn_v2")

    def test_run_ai_profile_task_initializes_model_api_client_with_runtime_credentials(self) -> None:
        seen_configs = []

        class FakeModelAPIClient:
            def __init__(self, *, api_key, base_url, model, temperature, timeout_seconds):
                seen_configs.append(
                    {
                        "api_key": api_key,
                        "base_url": base_url,
                        "model": model,
                        "temperature": temperature,
                        "timeout_seconds": timeout_seconds,
                    }
                )

            def analyze_profile(self, payload):
                return type(
                    "ModelResult",
                    (),
                    {
                        "content": {
                            "profile_summary": "",
                            "business_type": "",
                            "market_role": "",
                            "product_fit": "",
                            "customer_priority": "B",
                            "score_total": 70,
                            "score_breakdown": {},
                            "evidence": [],
                            "risk_flags": [],
                            "recommended_action": "",
                        },
                        "raw_response": {"id": "fake"},
                    },
                )()

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                domain = Domain(domain="client-model.example", website="https://client-model.example")
                session.add(domain)
                session.flush()
                package = ProfilePackage(
                    domain_record=domain,
                    schema_version="1.0",
                    crawl_status="success",
                    page_count=1,
                    payload_json={"company": {"domain": "client-model.example"}},
                    content_hash="c" * 64,
                )
                session.add(package)
                session.commit()
                package_id = package.id
            engine.dispose()

            with patch("tasks.handlers.ModelAPIClient", FakeModelAPIClient):
                run_ai_profile_task(
                    {
                        "database_url": database_url,
                        "profile_package_ids": [package_id],
                        "model_provider": "deepseek",
                        "api_base_url": "https://api.deepseek.com",
                        "api_key": "sk-runtime-secret",
                        "model_name": "deepseek-reasoner",
                        "temperature": 0.1,
                        "timeout_seconds": 44,
                    }
                )

        self.assertEqual(
            seen_configs,
            [
                {
                    "api_key": "sk-runtime-secret",
                    "base_url": "https://api.deepseek.com",
                    "model": "deepseek-reasoner",
                    "temperature": 0.1,
                    "timeout_seconds": 44.0,
                }
            ],
        )

    def test_run_ai_profile_task_does_not_persist_api_key_in_task_params(self) -> None:
        def fake_analyzer(payload, options):
            return {
                "profile_summary": "",
                "business_type": "",
                "market_role": "",
                "product_fit": "",
                "customer_priority": "B",
                "score_total": 70,
                "score_breakdown": {},
                "evidence": [],
                "risk_flags": [],
                "recommended_action": "",
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                domain = Domain(domain="secret.example", website="https://secret.example")
                session.add(domain)
                session.flush()
                package = ProfilePackage(
                    domain_record=domain,
                    schema_version="1.0",
                    crawl_status="success",
                    page_count=1,
                    payload_json={"company": {"domain": "secret.example"}},
                    content_hash="d" * 64,
                )
                session.add(package)
                session.commit()
                package_id = package.id
            engine.dispose()

            run_ai_profile_task(
                {
                    "database_url": database_url,
                    "profile_package_ids": [package_id],
                    "model_provider": "deepseek",
                    "model_name": "deepseek-chat",
                    "api_base_url": "https://api.deepseek.com",
                    "api_key": "sk-never-store",
                },
                analyzer=fake_analyzer,
            )

            engine = create_engine_from_url(database_url)
            Session = create_session_factory(engine)
            with Session() as session:
                task_run = session.query(TaskRun).one()
                qualified_lead_count = session.query(QualifiedLead).count()
            engine.dispose()

        self.assertNotIn("api_key", task_run.params_json)
        self.assertEqual(task_run.params_json["api_key_configured"], True)
        self.assertEqual(qualified_lead_count, 0)

    def test_run_ai_profile_task_uses_default_database_url_when_not_supplied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                domain = Domain(domain="default-db.example", website="https://default-db.example")
                session.add(domain)
                session.flush()
                package = ProfilePackage(
                    domain_record=domain,
                    schema_version="1.0",
                    crawl_status="success",
                    page_count=1,
                    payload_json={"company": {"domain": "default-db.example"}},
                    content_hash="e" * 64,
                )
                session.add(package)
                session.commit()
                package_id = package.id
            engine.dispose()

            def fake_analyzer(payload, options):
                return {
                    "profile_summary": "",
                    "business_type": "",
                    "market_role": "",
                    "product_fit": "",
                    "customer_priority": "C",
                    "score_total": 50,
                    "score_breakdown": {},
                    "evidence": [],
                    "risk_flags": [],
                    "recommended_action": "",
                }

            with patch("tasks.handlers.DEFAULT_DATABASE_URL", database_url):
                summary = run_ai_profile_task(
                    {
                        "profile_package_ids": [package_id],
                        "model_provider": "deepseek",
                        "model_name": "deepseek-chat",
                        "api_base_url": "https://api.deepseek.com",
                        "api_key": "sk-task-secret",
                    },
                    analyzer=fake_analyzer,
                )

        self.assertEqual(summary["results_created"], 1)

    def test_run_ai_profile_task_can_select_profile_packages_by_source_group(self) -> None:
        calls = []

        def fake_analyzer(payload, options):
            calls.append({"payload": payload, "options": options})
            return {
                "profile_summary": "Pool heat pump lead",
                "business_type": "installer",
                "market_role": "contractor",
                "product_fit": "high",
                "customer_priority": "B",
                "score_total": 72,
                "score_breakdown": {},
                "evidence": [],
                "risk_flags": [],
                "recommended_action": "",
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                crawl_run = TaskRun(task_type="crawl", name="Crawl Italy Pool", status="success")
                acme = Domain(domain="acme.example", website="https://acme.example")
                beta = Domain(domain="beta.example", website="https://beta.example")
                session.add_all([crawl_run, acme, beta])
                session.flush()
                session.add_all(
                    [
                        ProfilePackage(
                            domain_record=acme,
                            crawl_task_run_id=crawl_run.id,
                            schema_version="1.0",
                            crawl_status="success",
                            page_count=1,
                            payload_json={"company": {"domain": "acme.example"}},
                            content_hash="f" * 64,
                        ),
                        ProfilePackage(
                            domain_record=beta,
                            crawl_task_run_id=crawl_run.id,
                            schema_version="1.0",
                            crawl_status="success",
                            page_count=1,
                            payload_json={"company": {"domain": "beta.example"}},
                            content_hash="g" * 64,
                        ),
                    ]
                )
                session.commit()
                crawl_run_id = crawl_run.id
            engine.dispose()

            summary = run_ai_profile_task(
                {
                    "database_url": database_url,
                    "profile_source_group_id": crawl_run_id,
                    "model_provider": "deepseek",
                    "model_name": "deepseek-v4-pro",
                    "api_base_url": "https://api.deepseek.com",
                    "api_key": "sk-task-secret",
                },
                analyzer=fake_analyzer,
            )

            engine = create_engine_from_url(database_url)
            Session = create_session_factory(engine)
            with Session() as session:
                result_count = session.query(AIProfileResult).count()
                task_items = session.query(TaskItem).filter(TaskItem.item_type == "profile_package").all()
            engine.dispose()

        self.assertEqual(summary["profile_source_group_id"], crawl_run_id)
        self.assertEqual(summary["profile_packages"], 2)
        self.assertEqual(summary["results_created"], 2)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result_count, 2)
        self.assertEqual(len(task_items), 2)

    def test_run_search_task_calls_search_runner_and_returns_count(self) -> None:
        calls = []

        def fake_search_runner(**kwargs):
            calls.append(kwargs)
            return [{"domain": "one.example"}, {"domain": "two.example"}]

        summary = run_search_task(
            {
                "config_path": "config/keywords_france.yaml",
                "output_file": "company_websites_france.csv",
                "state_dir": ".search_state_france",
                "engines": "duckduckgo,bing",
                "backend": "requests",
                "max_pages": 1,
                "limit_keywords": 2,
                "keyword_delay_seconds": 0,
                "persist_to_database": False,
            },
            search_runner=fake_search_runner,
        )

        self.assertEqual(summary["rows"], 2)
        self.assertEqual(summary["output_file"], "company_websites_france.csv")
        self.assertEqual(summary["state_dir"], ".search_state_france")
        self.assertEqual(calls[0]["engine_names"], ["duckduckgo", "bing"])
        self.assertEqual(calls[0]["backend"], "requests")
        self.assertEqual(calls[0]["limit_keywords"], 2)

    def test_run_search_task_persists_rows_to_database_when_database_url_is_provided(self) -> None:
        calls = []

        def fake_search_runner(**kwargs):
            calls.append(kwargs)
            return [
                {
                    "keyword": "pool heat pump France",
                    "title": "Acme France",
                    "website": "https://www.acme.example/fr",
                    "domain": "acme.example",
                    "source_url": "https://search.local/fr",
                    "engine": "duckduckgo",
                    "country": "France",
                }
            ]

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            summary = run_search_task(
                {
                    "database_url": database_url,
                    "output_file": "company_websites_france.csv",
                    "persist_to_database": True,
                },
                search_runner=fake_search_runner,
            )

            engine = create_engine_from_url(database_url)
            Session = create_session_factory(engine)
            with Session() as session:
                domain_count = session.query(Domain).count()
                search_count = session.query(SearchResult).count()
            engine.dispose()

        self.assertTrue(summary["database_persisted"])
        self.assertEqual(calls[0]["output_file"], "company_websites_france.csv")
        self.assertEqual(summary["database_import"]["search_results_created"], 1)
        self.assertEqual(domain_count, 1)
        self.assertEqual(search_count, 1)

    def test_run_search_task_can_persist_to_database_without_csv_output(self) -> None:
        calls = []

        def fake_search_runner(**kwargs):
            calls.append(kwargs)
            return [
                {
                    "keyword": "pool heat pump France",
                    "title": "Acme France",
                    "website": "https://www.acme.example/fr",
                    "domain": "acme.example",
                    "source_url": "https://search.local/fr",
                    "engine": "duckduckgo",
                    "country": "France",
                }
            ]

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            summary = run_search_task(
                {
                    "database_url": database_url,
                    "state_dir": "",
                    "persist_to_database": True,
                },
                search_runner=fake_search_runner,
            )

        self.assertIsNone(calls[0]["output_file"])
        self.assertIsNone(calls[0]["state_dir"])
        self.assertEqual(summary["output_file"], "")
        self.assertNotIn("state_dir", summary)
        self.assertTrue(summary["database_persisted"])
        self.assertEqual(summary["database_import"]["search_results_created"], 1)

    def test_run_search_task_loads_keyword_specs_from_database_keyword_group(self) -> None:
        calls = []

        def fake_search_runner(**kwargs):
            calls.append(kwargs)
            specs = kwargs["keyword_specs"]
            return [
                {
                    "keyword": specs[0].keyword,
                    "title": "Acme France",
                    "website": "https://www.acme.example/fr",
                    "domain": "acme.example",
                    "source_url": "https://search.local/fr",
                    "engine": "duckduckgo",
                    "country": specs[0].country,
                    "country_term": specs[0].country_term,
                    "industry": specs[0].industry,
                    "industry_term": specs[0].industry_term,
                }
            ]

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                group = KeywordGroup(
                    name="France Pool",
                    country="France",
                    country_terms="France",
                    keyword_terms="pool heat pump",
                    notes="",
                    is_active=True,
                )
                session.add(group)
                session.commit()
                group_id = group.id
            engine.dispose()

            summary = run_search_task(
                {
                    "database_url": database_url,
                    "keyword_group_id": group_id,
                    "limit_keywords": 1,
                    "persist_to_database": True,
                },
                search_runner=fake_search_runner,
            )

        self.assertEqual(calls[0]["keyword_specs"][0].keyword, "pool heat pump France")
        self.assertEqual(calls[0]["keyword_specs"][0].industry, "France Pool")
        self.assertTrue(summary["database_persisted"])

    def test_run_search_task_records_database_task_batch(self) -> None:
        calls = []

        def fake_search_runner(**kwargs):
            calls.append(kwargs)
            specs = kwargs["keyword_specs"]
            kwargs["on_keyword_done"](
                {
                    "keyword": specs[0].keyword,
                    "status": "success",
                    "added": 1,
                    "result_count": 1,
                    "total_unique_domains": 1,
                }
            )
            return [
                {
                    "keyword": specs[0].keyword,
                    "title": "Acme France",
                    "website": "https://www.acme.example/fr",
                    "domain": "acme.example",
                    "source_url": "https://search.local/fr",
                    "engine": "duckduckgo",
                    "country": specs[0].country,
                }
            ]

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                group = KeywordGroup(
                    name="France Pool",
                    country="France",
                    country_terms="France",
                    keyword_terms="pool heat pump",
                    notes="",
                    is_active=True,
                )
                session.add(group)
                session.commit()
                group_id = group.id
            engine.dispose()

            summary = run_search_task(
                {
                    "database_url": database_url,
                    "keyword_group_id": group_id,
                    "limit_keywords": 1,
                    "persist_to_database": True,
                },
                search_runner=fake_search_runner,
            )

            engine = create_engine_from_url(database_url)
            Session = create_session_factory(engine)
            with Session() as session:
                task_run = session.query(TaskRun).one()
                task_item = session.query(TaskItem).one()
            engine.dispose()

        self.assertIsNone(calls[0]["state_dir"])
        self.assertNotIn("state_dir", summary)
        self.assertEqual(summary["task_run_id"], task_run.id)
        self.assertEqual(task_run.task_type, "search")
        self.assertEqual(task_run.status, "success")
        self.assertEqual(task_item.item_type, "keyword")
        self.assertEqual(task_item.item_key, "pool heat pump France")
        self.assertEqual(task_item.status, "success")

    def test_run_search_task_finishes_as_cancelled_when_cancel_requested(self) -> None:
        calls = []

        def fake_search_runner(**kwargs):
            calls.append(kwargs)
            specs = kwargs["keyword_specs"]
            kwargs["on_keyword_done"](
                {
                    "keyword": specs[0].keyword,
                    "status": "success",
                    "added": 1,
                    "result_count": 1,
                    "total_unique_domains": 1,
                }
            )
            self.assertFalse(kwargs["should_cancel"]())
            engine = create_engine_from_url(database_url)
            Session = create_session_factory(engine)
            with Session() as session:
                task_run = session.query(TaskRun).one()
                task_run.status = "cancelling"
                session.commit()
            engine.dispose()
            self.assertTrue(kwargs["should_cancel"]())
            return [
                {
                    "keyword": specs[0].keyword,
                    "title": "Acme Italy",
                    "website": "https://acme.example/it",
                    "domain": "acme.example",
                    "source_url": "https://search.local/it",
                    "engine": "bing",
                    "country": specs[0].country,
                }
            ]

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                group = KeywordGroup(
                    name="Italy Pool",
                    country="Italy",
                    country_terms="Italy",
                    keyword_terms="pool heat pump",
                    notes="",
                    is_active=True,
                )
                session.add(group)
                session.commit()
                group_id = group.id
            engine.dispose()

            summary = run_search_task(
                {
                    "database_url": database_url,
                    "keyword_group_id": group_id,
                    "persist_to_database": True,
                },
                search_runner=fake_search_runner,
            )

            engine = create_engine_from_url(database_url)
            Session = create_session_factory(engine)
            with Session() as session:
                task_run = session.query(TaskRun).one()
            engine.dispose()

        self.assertTrue(callable(calls[0]["should_cancel"]))
        self.assertEqual(summary["task_run_status"], "cancelled")
        self.assertEqual(task_run.status, "cancelled")

    def test_run_search_task_creates_candidate_group_from_search_output(self) -> None:
        def fake_search_runner(**kwargs):
            specs = kwargs["keyword_specs"]
            return [
                {
                    "keyword": specs[0].keyword,
                    "title": "Acme France",
                    "website": "https://www.acme.example/fr",
                    "domain": "acme.example",
                    "source_url": "https://search.local/fr",
                    "engine": "duckduckgo",
                    "country": specs[0].country,
                }
            ]

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                group = KeywordGroup(
                    name="France Pool",
                    country="France",
                    country_terms="France",
                    keyword_terms="pool heat pump",
                    notes="",
                    is_active=True,
                )
                session.add(group)
                session.commit()
                group_id = group.id
            engine.dispose()

            summary = run_search_task(
                {
                    "database_url": database_url,
                    "keyword_group_id": group_id,
                    "limit_keywords": 1,
                    "persist_to_database": True,
                },
                search_runner=fake_search_runner,
            )

            engine = create_engine_from_url(database_url)
            Session = create_session_factory(engine)
            with Session() as session:
                candidate_group = session.query(CandidateGroup).one()
                candidate_item = session.query(CandidateGroupItem).one()
                candidate_item_domain = candidate_item.domain_record.domain
            engine.dispose()

        self.assertEqual(summary["candidate_group_id"], candidate_group.id)
        self.assertEqual(candidate_group.source_task_run_id, summary["task_run_id"])
        self.assertEqual(candidate_group.keyword_group_id, group_id)
        self.assertEqual(candidate_group.country, "France")
        self.assertEqual(candidate_item_domain, "acme.example")

    def test_run_crawl_task_calls_crawl_runner_and_returns_status_counts(self) -> None:
        calls = []

        def fake_crawl_runner(**kwargs):
            calls.append(kwargs)
            return [{"status": "success"}, {"status": "empty"}, {"status": "success"}]

        summary = run_crawl_task(
            {
                "input_file": "company_websites_france.csv",
                "output_file": "company_info_france.csv",
                "state_dir": ".crawl_state_france",
                "backend": "requests",
                "workers": 3,
                "max_depth": 2,
                "max_pages_per_site": 12,
                "profile_input_dir": "profile_inputs/france",
                "persist_to_database": False,
            },
            crawl_runner=fake_crawl_runner,
        )

        self.assertEqual(summary["rows"], 3)
        self.assertEqual(summary["status_counts"], {"success": 2, "empty": 1})
        self.assertEqual(summary["state_dir"], ".crawl_state_france")
        self.assertEqual(calls[0]["input_file"], "company_websites_france.csv")
        self.assertEqual(calls[0]["profile_input_dir"], "profile_inputs/france")

    def test_run_crawl_task_persists_rows_to_database_when_database_url_is_provided(self) -> None:
        def fake_crawl_runner(**kwargs):
            return [
                {
                    "keyword": "pool heat pump France",
                    "company_name": "Acme Pool Heating",
                    "website": "https://acme.example",
                    "domain": "acme.example",
                    "emails": "sales@acme.example",
                    "phones": "+33 1 23 45 67 89",
                    "possible_address": "12 Rue Example, Paris",
                    "description": "Distributor of swimming pool heat pumps.",
                    "crawled_pages": "https://acme.example",
                    "status": "success",
                    "social_links": "",
                    "country": "France",
                }
            ]

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            profile_dir = Path(temp_dir) / "profile_inputs"
            profile_dir.mkdir()
            summary = run_crawl_task(
                {
                    "database_url": database_url,
                    "input_file": "company_websites_france.csv",
                    "output_file": "company_info_france.csv",
                    "profile_input_dir": str(profile_dir),
                    "persist_to_database": True,
                },
                crawl_runner=fake_crawl_runner,
            )

            engine = create_engine_from_url(database_url)
            Session = create_session_factory(engine)
            with Session() as session:
                domain_count = session.query(Domain).count()
                crawl_count = session.query(CrawlResult).count()
                contact_count = session.query(Contact).count()
            engine.dispose()

        self.assertTrue(summary["database_persisted"])
        self.assertEqual(summary["database_import"]["crawl_results_created"], 1)
        self.assertEqual(summary["database_import"]["contacts_created"], 2)
        self.assertEqual(domain_count, 1)
        self.assertEqual(crawl_count, 1)
        self.assertEqual(contact_count, 2)

    def test_run_crawl_task_selects_database_candidates_when_no_input_file_is_provided(self) -> None:
        calls = []

        def fake_crawl_runner(**kwargs):
            calls.append(kwargs)
            companies = kwargs["companies"]
            return [
                {
                    "keyword": companies[0].keyword,
                    "company_name": companies[0].title,
                    "website": companies[0].website,
                    "domain": companies[0].domain,
                    "emails": "sales@acme.example",
                    "phones": "",
                    "possible_address": "",
                    "description": "Pool heat pump distributor",
                    "crawled_pages": companies[0].website,
                    "status": "success",
                    "error": "",
                    "social_links": "",
                    "contacts": "",
                    "page_categories": "",
                    "country": companies[0].country,
                    "industry": companies[0].industry,
                    "matched_keywords": companies[0].matched_keywords,
                    "matched_countries": companies[0].matched_countries,
                    "matched_industries": companies[0].matched_industries,
                    "matched_industry_terms": companies[0].matched_industry_terms,
                }
            ]

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                acme = Domain(domain="acme.example", website="https://acme.example", display_name="Acme")
                beta = Domain(domain="beta.example", website="https://beta.example", display_name="Beta")
                session.add_all([acme, beta])
                session.flush()
                session.add_all(
                    [
                        SearchResult(
                            domain_record=acme,
                            keyword="pool heat pump France",
                            title="Acme Pool Heating",
                            website="https://acme.example",
                            country="France",
                            industry="pool_heat_pump",
                            matched_keywords="pool heat pump France",
                            matched_countries="France",
                            matched_industries="pool_heat_pump",
                        ),
                        SearchResult(
                            domain_record=beta,
                            keyword="HVAC France",
                            title="Beta HVAC",
                            website="https://beta.example",
                            country="France",
                        ),
                        CrawlResult(domain_record=beta, status="success", source_file="previous"),
                        CountrySignal(
                            domain_record=acme,
                            country="France",
                            signal_type="search_country",
                            confidence=0.4,
                            source="task:search",
                        ),
                    ]
                )
                session.commit()
            engine.dispose()

            summary = run_crawl_task(
                {
                    "database_url": database_url,
                    "candidate_country": "France",
                    "candidate_limit": 10,
                    "output_file": "",
                    "profile_input_dir": str(Path(temp_dir) / "profile_inputs"),
                    "persist_to_database": True,
                },
                crawl_runner=fake_crawl_runner,
            )

        self.assertEqual([company.domain for company in calls[0]["companies"]], ["acme.example"])
        self.assertEqual(summary["rows"], 1)
        self.assertTrue(summary["database_persisted"])

    def test_run_crawl_task_selects_candidates_from_candidate_group(self) -> None:
        calls = []

        def fake_crawl_runner(**kwargs):
            calls.append(kwargs)
            return [
                {
                    "keyword": company.keyword,
                    "company_name": company.title,
                    "website": company.website,
                    "domain": company.domain,
                    "emails": "",
                    "phones": "",
                    "possible_address": "",
                    "description": "",
                    "crawled_pages": company.website,
                    "status": "success",
                    "error": "",
                    "social_links": "",
                    "contacts": "",
                    "page_categories": "",
                    "country": company.country,
                    "industry": company.industry,
                    "matched_keywords": company.matched_keywords,
                    "matched_countries": company.matched_countries,
                    "matched_industries": company.matched_industries,
                    "matched_industry_terms": company.matched_industry_terms,
                }
                for company in kwargs["companies"]
            ]

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            group_rows = [
                task_search_row("pool heat pump France", "Acme", "https://acme.example", "acme.example"),
                task_search_row("pool heat pump France", "Beta", "https://beta.example", "beta.example"),
            ]
            extra_rows = [
                task_search_row("pool heat pump France", "Gamma", "https://gamma.example", "gamma.example"),
            ]
            with Session() as session:
                import_search_rows(session, group_rows, source_name="task:search:group")
                import_search_rows(session, extra_rows, source_name="task:search:extra")
                session.flush()
                candidate_group = create_candidate_group_from_search_rows(
                    session,
                    rows=group_rows,
                    source_name="task:search:group",
                    name="France selected group",
                    country="France",
                )
                session.commit()
                candidate_group_id = candidate_group.id
            engine.dispose()

            summary = run_crawl_task(
                {
                    "database_url": database_url,
                    "candidate_group_id": candidate_group_id,
                    "candidate_limit": 10,
                    "profile_input_dir": str(Path(temp_dir) / "profile_inputs"),
                    "persist_to_database": True,
                },
                crawl_runner=fake_crawl_runner,
            )

        self.assertEqual([company.domain for company in calls[0]["companies"]], ["acme.example", "beta.example"])
        self.assertEqual(summary["candidate_group_id"], candidate_group_id)
        self.assertEqual(summary["rows"], 2)
        self.assertTrue(summary["database_persisted"])

    def test_run_crawl_task_records_database_task_batch(self) -> None:
        calls = []

        def fake_crawl_runner(**kwargs):
            calls.append(kwargs)
            companies = kwargs["companies"]
            kwargs["on_domain_done"](
                {
                    "domain": companies[0].domain,
                    "status": "success",
                    "company_name": companies[0].title,
                }
            )
            return [
                {
                    "keyword": companies[0].keyword,
                    "company_name": companies[0].title,
                    "website": companies[0].website,
                    "domain": companies[0].domain,
                    "emails": "",
                    "phones": "",
                    "possible_address": "",
                    "description": "Pool heat pump distributor",
                    "crawled_pages": companies[0].website,
                    "status": "success",
                    "error": "",
                    "social_links": "",
                    "contacts": "",
                    "page_categories": "",
                    "country": companies[0].country,
                    "industry": companies[0].industry,
                    "matched_keywords": companies[0].matched_keywords,
                    "matched_countries": companies[0].matched_countries,
                    "matched_industries": companies[0].matched_industries,
                    "matched_industry_terms": companies[0].matched_industry_terms,
                }
            ]

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                acme = Domain(domain="acme.example", website="https://acme.example", display_name="Acme")
                session.add(acme)
                session.flush()
                session.add_all(
                    [
                        SearchResult(
                            domain_record=acme,
                            keyword="pool heat pump France",
                            title="Acme Pool Heating",
                            website="https://acme.example",
                            country="France",
                            matched_countries="France",
                        ),
                        CountrySignal(
                            domain_record=acme,
                            country="France",
                            signal_type="search_country",
                            confidence=0.4,
                            source="task:search",
                        ),
                    ]
                )
                session.commit()
            engine.dispose()

            summary = run_crawl_task(
                {
                    "database_url": database_url,
                    "candidate_country": "France",
                    "candidate_limit": 10,
                    "state_dir": "",
                    "profile_input_dir": str(Path(temp_dir) / "profile_inputs"),
                    "persist_to_database": True,
                },
                crawl_runner=fake_crawl_runner,
            )

            engine = create_engine_from_url(database_url)
            Session = create_session_factory(engine)
            with Session() as session:
                task_run = session.query(TaskRun).one()
                task_item = session.query(TaskItem).one()
            engine.dispose()

        self.assertIsNone(calls[0]["state_dir"])
        self.assertNotIn("state_dir", summary)
        self.assertEqual(summary["task_run_id"], task_run.id)
        self.assertEqual(task_run.task_type, "crawl")
        self.assertEqual(task_run.status, "success")
        self.assertEqual(task_item.item_type, "domain")
        self.assertEqual(task_item.item_key, "acme.example")
        self.assertEqual(task_item.status, "success")

    def test_run_crawl_task_passes_cancel_checker_to_crawl_runner(self) -> None:
        calls = []

        def fake_crawl_runner(**kwargs):
            calls.append(kwargs)
            self.assertFalse(kwargs["should_cancel"]())
            return []

        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite:///{Path(temp_dir) / 'leadgen.db'}"
            engine = create_engine_from_url(database_url)
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                acme = Domain(domain="acme.example", website="https://acme.example", display_name="Acme")
                session.add(acme)
                session.flush()
                session.add(SearchResult(domain_record=acme, keyword="pool heat pump Italy", website="https://acme.example"))
                session.commit()
            engine.dispose()

            run_crawl_task(
                {
                    "database_url": database_url,
                    "candidate_limit": 1,
                    "persist_to_database": True,
                },
                crawl_runner=fake_crawl_runner,
            )

        self.assertTrue(callable(calls[0]["should_cancel"]))

    def test_run_crawl_task_builds_fetcher_configs_from_runtime_params(self) -> None:
        calls = []

        def fake_crawl_runner(**kwargs):
            calls.append(kwargs)
            return []

        run_crawl_task(
            {
                "backend": "browser",
                "global_delay": 1.5,
                "domain_delay": 3.0,
                "max_retries": 2,
                "backoff_base": 1.0,
                "backoff_max": 20.0,
                "proxy": "http://127.0.0.1:7890",
                "use_system_proxy": False,
                "headless": False,
                "browser_max_pages": 2,
                "browser_timeout_ms": 10000,
                "browser_wait_ms": 500,
                "persist_to_database": False,
            },
            crawl_runner=fake_crawl_runner,
        )

        fetcher_config = calls[0]["fetcher_config"]
        browser_config = calls[0]["browser_fetch_config"]
        self.assertEqual(fetcher_config.global_min_interval_seconds, 1.5)
        self.assertEqual(fetcher_config.domain_min_interval_seconds, 3.0)
        self.assertEqual(fetcher_config.max_retries, 2)
        self.assertEqual(fetcher_config.proxy_url, "http://127.0.0.1:7890")
        self.assertFalse(fetcher_config.use_system_proxy)
        self.assertFalse(browser_config.headless)
        self.assertEqual(browser_config.max_pages, 2)
        self.assertEqual(browser_config.timeout_ms, 10000)
        self.assertEqual(browser_config.wait_ms, 500)

    def test_run_import_existing_data_task_resolves_sources_and_returns_import_summary(self) -> None:
        calls = []

        def fake_import_sources(database_url, search_csvs, crawl_csvs, profile_dirs, create_tables):
            calls.append(
                {
                    "database_url": database_url,
                    "search_csvs": search_csvs,
                    "crawl_csvs": crawl_csvs,
                    "profile_dirs": profile_dirs,
                    "create_tables": create_tables,
                }
            )
            return {
                "domains_created": 1,
                "search_results_created": 2,
                "crawl_results_created": 3,
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            search_csv = root / "company_websites_france.csv"
            crawl_csv = root / "company_info_france.csv"
            profile_dir = root / "profile_inputs" / "france"
            search_csv.write_text("domain\nexample.com\n", encoding="utf-8")
            crawl_csv.write_text("domain\nexample.com\n", encoding="utf-8")
            profile_dir.mkdir(parents=True)

            summary = run_import_existing_data_task(
                {
                    "database_url": "sqlite:///fixture.db",
                    "search_csvs": [str(search_csv)],
                    "crawl_csvs": [str(crawl_csv)],
                    "profile_dirs": [str(profile_dir)],
                    "create_tables": False,
                },
                root=root,
                import_sources_func=fake_import_sources,
            )

        self.assertEqual(summary["domains_created"], 1)
        self.assertEqual(calls[0]["database_url"], "sqlite:///fixture.db")
        self.assertEqual(calls[0]["search_csvs"], [search_csv])
        self.assertEqual(calls[0]["crawl_csvs"], [crawl_csv])
        self.assertEqual(calls[0]["profile_dirs"], [profile_dir])
        self.assertFalse(calls[0]["create_tables"])


def task_search_row(keyword: str, title: str, website: str, domain: str) -> dict[str, str]:
    return {
        "keyword": keyword,
        "title": title,
        "website": website,
        "domain": domain,
        "source_url": "https://search.local",
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
