import unittest

from tasks.runner import run_task


class TaskRunnerTests(unittest.TestCase):
    def test_run_task_returns_success_result_with_summary(self) -> None:
        def handler(params):
            return {"rows": params["rows"]}

        result = run_task("fixture", handler, {"rows": 3})

        self.assertEqual(result.task_type, "fixture")
        self.assertEqual(result.status, "success")
        self.assertEqual(result.params, {"rows": 3})
        self.assertEqual(result.summary, {"rows": 3})
        self.assertEqual(result.error, "")
        self.assertGreaterEqual(result.duration_seconds, 0)
        self.assertIn("started_at", result.to_dict())
        self.assertIn("finished_at", result.to_dict())

    def test_run_task_uses_database_task_status_when_handler_reports_cancellation(self) -> None:
        def handler(params):
            return {"rows": 1, "task_run_status": "cancelled"}

        result = run_task("search", handler, {})

        self.assertEqual(result.status, "cancelled")
        self.assertEqual(result.summary["task_run_status"], "cancelled")

    def test_run_task_catches_handler_errors_without_database_state(self) -> None:
        def handler(params):
            raise RuntimeError(f"bad {params['value']}")

        result = run_task("fixture", handler, {"value": "input"})

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.summary, {})
        self.assertIn("RuntimeError: bad input", result.error)


if __name__ == "__main__":
    unittest.main()
