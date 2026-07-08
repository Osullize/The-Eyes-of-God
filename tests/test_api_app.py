import unittest
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app, execution_mode_from_env
from api.schemas import AIProfileTaskRequest
from database.models import TaskRun
from database.session import create_all, create_engine_from_url, create_session_factory


class FastApiAppTests(unittest.TestCase):
    def test_execution_mode_from_env_defaults_to_inline_and_accepts_celery(self) -> None:
        self.assertEqual(execution_mode_from_env({}), "inline")
        self.assertEqual(execution_mode_from_env({"TASK_EXECUTION_MODE": "celery"}), "celery")
        self.assertEqual(execution_mode_from_env({"TASK_EXECUTION_MODE": "bad"}), "inline")

    def test_health_endpoint_reports_ok(self) -> None:
        client = TestClient(create_app())

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_runtime_endpoint_reports_task_execution_mode(self) -> None:
        client = TestClient(create_app(execution_mode="celery"))

        response = client.get("/runtime")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"task_execution_mode": "celery"})

    def test_ai_profile_request_defaults_to_business_knowledge_prompt(self) -> None:
        request = AIProfileTaskRequest(profile_package_ids=[101])

        self.assertEqual(request.model_provider, "deepseek")
        self.assertEqual(request.api_base_url, "https://api.deepseek.com")
        self.assertEqual(request.model_name, "deepseek-v4-pro")
        self.assertEqual(request.temperature, 0.2)
        self.assertEqual(request.timeout_seconds, 180.0)
        self.assertFalse(hasattr(request, "prompt_version"))

    def test_local_vue_console_origin_is_allowed_by_cors(self) -> None:
        client = TestClient(create_app())

        response = client.get("/health", headers={"Origin": "http://127.0.0.1:5173"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://127.0.0.1:5173")

    def test_import_existing_data_endpoint_runs_injected_handler(self) -> None:
        calls = []

        def handler(params):
            calls.append(params)
            return {"domains_created": 2}

        client = TestClient(create_app(handlers={"import_existing_data": handler}))

        response = client.post(
            "/tasks/import-existing-data",
            json={
                "database_url": "sqlite:///fixture.db",
                "search_csvs": ["company_websites_france.csv"],
                "crawl_csvs": ["company_info_france.csv"],
                "profile_dirs": ["profile_inputs/france"],
                "create_tables": False,
            },
        )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["task_type"], "import_existing_data")
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["summary"], {"domains_created": 2})
        self.assertEqual(calls[0]["database_url"], "sqlite:///fixture.db")
        self.assertEqual(calls[0]["search_csvs"], ["company_websites_france.csv"])
        self.assertFalse(calls[0]["create_tables"])

    def test_crawl_endpoint_returns_failed_task_result_without_raising_http_500(self) -> None:
        def handler(params):
            raise RuntimeError("crawl failed")

        client = TestClient(create_app(handlers={"crawl": handler}))

        response = client.post(
            "/tasks/crawl",
            json={
                "input_file": "company_websites_france.csv",
                "output_file": "company_info_france.csv",
                "backend": "requests",
            },
        )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["task_type"], "crawl")
        self.assertEqual(body["status"], "failed")
        self.assertIn("RuntimeError: crawl failed", body["error"])

    def test_search_endpoint_runs_injected_handler(self) -> None:
        calls = []

        def handler(params):
            calls.append(params)
            return {"rows": 3}

        client = TestClient(create_app(handlers={"search": handler}))

        response = client.post(
            "/tasks/search",
            json={
                "keyword_group_id": 7,
                "backend": "requests",
                "max_pages": 1,
                "limit_keywords": 2,
            },
        )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["task_type"], "search")
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["summary"], {"rows": 3})
        self.assertEqual(calls[0]["limit_keywords"], 2)
        self.assertEqual(calls[0]["keyword_group_id"], 7)

    def test_ai_profile_endpoint_runs_injected_handler(self) -> None:
        calls = []

        def handler(params):
            calls.append(params)
            return {"profile_packages": 2, "results_created": 2}

        client = TestClient(create_app(handlers={"ai_profile": handler}))

        response = client.post(
            "/tasks/ai-profile",
            json={
                "profile_package_ids": [101, 102],
                "model_provider": "deepseek",
                "api_base_url": "https://api.deepseek.com",
                "api_key": "sk-request-secret",
                "model_name": "deepseek-chat",
                "temperature": 0.1,
                "timeout_seconds": 60,
            },
        )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["task_type"], "ai_profile")
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["summary"], {"profile_packages": 2, "results_created": 2})
        self.assertEqual(calls[0]["profile_package_ids"], [101, 102])
        self.assertEqual(calls[0]["model_provider"], "deepseek")
        self.assertEqual(calls[0]["api_key"], "sk-request-secret")
        self.assertNotIn("prompt_version", calls[0])

    def test_ai_profile_endpoint_accepts_profile_source_group_id(self) -> None:
        calls = []

        def handler(params):
            calls.append(params)
            return {"profile_source_group_id": 12, "profile_packages": 3}

        client = TestClient(create_app(handlers={"ai_profile": handler}))

        response = client.post(
            "/tasks/ai-profile",
            json={
                "profile_source_group_id": 12,
                "model_provider": "deepseek",
                "api_base_url": "https://api.deepseek.com",
                "api_key": "sk-request-secret",
                "model_name": "deepseek-v4-pro",
            },
        )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["task_type"], "ai_profile")
        self.assertEqual(body["summary"]["profile_source_group_id"], 12)
        self.assertEqual(calls[0]["profile_source_group_id"], 12)
        self.assertNotIn("profile_package_ids", calls[0])

    def test_cancel_task_run_endpoint_marks_running_task_cancelling(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = create_engine_from_url(f"sqlite:///{Path(temp_dir) / 'leadgen.db'}")
            create_all(engine)
            Session = create_session_factory(engine)
            with Session() as session:
                task_run = TaskRun(task_type="search", name="Search Italy", status="running")
                session.add(task_run)
                session.commit()
                task_run_id = task_run.id

            client = TestClient(create_app(session_factory=Session))
            response = client.post(f"/task-runs/{task_run_id}/cancel")
            body = response.json()
            engine.dispose()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["id"], task_run_id)
        self.assertEqual(body["status"], "cancelling")

    def test_cancel_task_run_endpoint_returns_404_for_missing_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = create_engine_from_url(f"sqlite:///{Path(temp_dir) / 'leadgen.db'}")
            create_all(engine)
            Session = create_session_factory(engine)
            client = TestClient(create_app(session_factory=Session))

            response = client.post("/task-runs/999/cancel")
            engine.dispose()

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
