import unittest

from database.models import Domain, TaskItem, TaskRun
from database.session import create_all, create_engine_from_url, create_session_factory
from database.task_batches import (
    create_task_items,
    create_task_run,
    finish_task_item,
    finish_task_run,
    get_task_run_detail,
    is_task_run_cancel_requested,
    list_task_runs,
    request_task_run_cancel,
    start_task_item,
    start_task_run,
)


class TaskBatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine_from_url("sqlite:///:memory:")
        create_all(self.engine)
        self.Session = create_session_factory(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_task_run_and_items_can_be_created_and_serialized(self) -> None:
        with self.Session() as session:
            domain = Domain(domain="acme.example", website="https://acme.example")
            session.add(domain)
            session.flush()

            task_run = create_task_run(
                session,
                task_type="crawl",
                name="France crawl",
                params={"country": "France"},
            )
            create_task_items(
                session,
                task_run,
                [
                    {"item_type": "domain", "item_key": "acme.example", "domain_id": domain.id},
                    {"item_type": "domain", "item_key": "beta.example"},
                ],
            )
            session.commit()

            detail = get_task_run_detail(session, task_run.id)

        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["task_type"], "crawl")
        self.assertEqual(detail["name"], "France crawl")
        self.assertEqual(detail["params_json"], {"country": "France"})
        self.assertEqual(detail["item_counts"], {"pending": 2})
        self.assertEqual([item["item_key"] for item in detail["items"]], ["acme.example", "beta.example"])

    def test_task_item_lifecycle_updates_run_summary(self) -> None:
        with self.Session() as session:
            task_run = create_task_run(session, task_type="search", name="Search France")
            items = create_task_items(
                session,
                task_run,
                [
                    {"item_type": "keyword", "item_key": "pool heat pump France"},
                    {"item_type": "keyword", "item_key": "pool heating France"},
                ],
            )
            start_task_run(session, task_run.id)
            start_task_item(session, items[0].id)
            finish_task_item(session, items[0].id, status="success", result={"rows": 3})
            start_task_item(session, items[1].id)
            finish_task_item(session, items[1].id, status="failed", error="blocked")
            finish_task_run(session, task_run.id, status="partial_failed")
            session.commit()

            detail = get_task_run_detail(session, task_run.id)

        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["status"], "partial_failed")
        self.assertEqual(detail["item_counts"], {"failed": 1, "success": 1})
        self.assertEqual(detail["summary_json"], {"failed": 1, "success": 1})
        self.assertEqual(detail["items"][0]["result_json"], {"rows": 3})
        self.assertEqual(detail["items"][1]["error"], "blocked")

    def test_task_runs_can_be_listed_with_filters(self) -> None:
        with self.Session() as session:
            create_task_run(session, task_type="search", name="Search France", status="success")
            create_task_run(session, task_type="crawl", name="Crawl France", status="failed")
            session.commit()

            all_runs = list_task_runs(session)
            search_runs = list_task_runs(session, task_type="search")
            failed_runs = list_task_runs(session, status="failed")

        self.assertEqual(all_runs["total"], 2)
        self.assertEqual(search_runs["total"], 1)
        self.assertEqual(search_runs["items"][0]["task_type"], "search")
        self.assertEqual(failed_runs["items"][0]["status"], "failed")

    def test_request_task_run_cancel_marks_run_cancelling_and_pending_items_cancelled(self) -> None:
        with self.Session() as session:
            task_run = create_task_run(session, task_type="search", name="Search Italy")
            items = create_task_items(
                session,
                task_run,
                [
                    {"item_type": "keyword", "item_key": "pool heat pump Italy"},
                    {"item_type": "keyword", "item_key": "pool heater Italy"},
                ],
            )
            start_task_run(session, task_run.id)
            start_task_item(session, items[0].id)

            detail = request_task_run_cancel(session, task_run.id)
            session.commit()

            refreshed = get_task_run_detail(session, task_run.id)

        self.assertEqual(detail["status"], "cancelling")
        self.assertIsNotNone(refreshed)
        assert refreshed is not None
        self.assertEqual(refreshed["status"], "cancelling")
        self.assertEqual(refreshed["item_counts"], {"cancelled": 1, "running": 1})
        self.assertEqual(refreshed["items"][0]["status"], "running")
        self.assertEqual(refreshed["items"][1]["status"], "cancelled")
        self.assertTrue(refreshed["items"][1]["error"])

    def test_request_task_run_cancel_does_not_change_terminal_run(self) -> None:
        with self.Session() as session:
            task_run = create_task_run(session, task_type="search", name="Done", status="success")
            session.commit()

            detail = request_task_run_cancel(session, task_run.id)
            session.commit()

        self.assertEqual(detail["status"], "success")

    def test_cancelled_task_item_is_not_overwritten_by_late_progress_callback(self) -> None:
        with self.Session() as session:
            task_run = create_task_run(session, task_type="search", name="Search Italy")
            items = create_task_items(
                session,
                task_run,
                [{"item_type": "keyword", "item_key": "pool heat pump Italy"}],
            )
            start_task_run(session, task_run.id)
            request_task_run_cancel(session, task_run.id)

            start_task_item(session, items[0].id)
            finish_task_item(session, items[0].id, status="success", result={"rows": 3})
            session.commit()

            detail = get_task_run_detail(session, task_run.id)

        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["item_counts"], {"cancelled": 1})
        self.assertEqual(detail["items"][0]["status"], "cancelled")
        self.assertNotEqual(detail["items"][0]["result_json"], {"rows": 3})

    def test_is_task_run_cancel_requested_reads_current_status(self) -> None:
        with self.Session() as session:
            task_run = create_task_run(session, task_type="crawl", name="Crawl Italy")
            session.commit()

            before = is_task_run_cancel_requested(session, task_run.id)
            request_task_run_cancel(session, task_run.id)
            after = is_task_run_cancel_requested(session, task_run.id)

        self.assertFalse(before)
        self.assertTrue(after)


if __name__ == "__main__":
    unittest.main()
