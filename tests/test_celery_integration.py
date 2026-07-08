import unittest

from api.app import create_app
from fastapi.testclient import TestClient

from tasks.celery_tasks import execute_task


class FakeAsyncResult:
    def __init__(self, task_id: str, state: str = "PENDING", result=None) -> None:
        self.id = task_id
        self.state = state
        self.result = result


class FakeCeleryTask:
    def __init__(self) -> None:
        self.calls = []

    def delay(self, task_type, params):
        self.calls.append((task_type, params))
        return FakeAsyncResult("task-123")

    def AsyncResult(self, task_id):
        return FakeAsyncResult(task_id, state="SUCCESS", result={"status": "success"})


class CeleryIntegrationTests(unittest.TestCase):
    def test_execute_task_uses_shared_handler_registry(self) -> None:
        calls = []

        def handler(params):
            calls.append(params)
            return {"rows": params["rows"]}

        result = execute_task("search", {"rows": 5}, handlers={"search": handler})

        self.assertEqual(result["task_type"], "search")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"], {"rows": 5})
        self.assertEqual(calls, [{"rows": 5}])

    def test_create_app_can_enqueue_task_instead_of_running_inline(self) -> None:
        celery_task = FakeCeleryTask()
        client = TestClient(create_app(execution_mode="celery", celery_task=celery_task))

        response = client.post(
            "/tasks/search",
            json={"config_path": "config/keywords_france.yaml", "limit_keywords": 1},
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.json(),
            {
                "task_id": "task-123",
                "task_type": "search",
                "status": "queued",
            },
        )
        self.assertEqual(
            celery_task.calls,
            [("search", {"config_path": "config/keywords_france.yaml", "limit_keywords": 1, "retry_failed": False})],
        )

    def test_task_status_endpoint_reads_celery_result(self) -> None:
        celery_task = FakeCeleryTask()
        client = TestClient(create_app(execution_mode="celery", celery_task=celery_task))

        response = client.get("/tasks/task-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "task_id": "task-123",
                "status": "SUCCESS",
                "result": {"status": "success"},
            },
        )


if __name__ == "__main__":
    unittest.main()
