import unittest

from sqlalchemy import Text, inspect

from database.models import (
    AIProfileResult,
    CandidateGroup,
    CandidateGroupItem,
    CompanyProfile,
    KeywordGroup,
    LeadScore,
    ProfilePackage,
    QualifiedLead,
    TaskItem,
    TaskRun,
)
from database.session import create_all, create_engine_from_url


class DatabaseModelTests(unittest.TestCase):
    def test_stage_c_tables_are_registered_and_created(self) -> None:
        engine = create_engine_from_url("sqlite:///:memory:")
        try:
            create_all(engine)

            table_names = set(inspect(engine).get_table_names())

        finally:
            engine.dispose()

        self.assertIn(QualifiedLead.__tablename__, table_names)
        self.assertIn(CompanyProfile.__tablename__, table_names)
        self.assertIn(LeadScore.__tablename__, table_names)

    def test_ai_profile_result_table_is_registered_and_created(self) -> None:
        engine = create_engine_from_url("sqlite:///:memory:")
        try:
            create_all(engine)

            table_names = set(inspect(engine).get_table_names())
            columns = {column["name"]: column for column in inspect(engine).get_columns(AIProfileResult.__tablename__)}

        finally:
            engine.dispose()

        self.assertIn(AIProfileResult.__tablename__, table_names)
        self.assertIn("profile_package_id", columns)
        self.assertIn("task_run_id", columns)
        self.assertIn("task_item_id", columns)
        self.assertIn("model_provider", columns)
        self.assertIn("model_name", columns)
        self.assertIn("prompt_version", columns)
        self.assertIn("company_name", columns)
        self.assertIn("score_total", columns)
        self.assertIn("result_json", columns)
        self.assertIn("raw_response_json", columns)
        self.assertIsInstance(columns["company_name"]["type"], Text)
        self.assertIsInstance(columns["product_fit"]["type"], Text)

    def test_keyword_group_table_is_registered_and_created(self) -> None:
        engine = create_engine_from_url("sqlite:///:memory:")
        try:
            create_all(engine)

            table_names = set(inspect(engine).get_table_names())
            columns = {column["name"] for column in inspect(engine).get_columns(KeywordGroup.__tablename__)}

        finally:
            engine.dispose()

        self.assertIn(KeywordGroup.__tablename__, table_names)
        self.assertIn("product_terms", columns)
        self.assertIn("role_terms", columns)
        self.assertIn("search_templates", columns)

    def test_task_batch_tables_are_registered_and_created(self) -> None:
        engine = create_engine_from_url("sqlite:///:memory:")
        try:
            create_all(engine)

            table_names = set(inspect(engine).get_table_names())

        finally:
            engine.dispose()

        self.assertIn(TaskRun.__tablename__, table_names)
        self.assertIn(TaskItem.__tablename__, table_names)

    def test_candidate_group_tables_are_registered_and_created(self) -> None:
        engine = create_engine_from_url("sqlite:///:memory:")
        try:
            create_all(engine)

            table_names = set(inspect(engine).get_table_names())

        finally:
            engine.dispose()

        self.assertIn(CandidateGroup.__tablename__, table_names)
        self.assertIn(CandidateGroupItem.__tablename__, table_names)

    def test_profile_package_table_stores_json_payload_and_group_indexes(self) -> None:
        engine = create_engine_from_url("sqlite:///:memory:")
        try:
            create_all(engine)

            columns = {column["name"] for column in inspect(engine).get_columns(ProfilePackage.__tablename__)}

        finally:
            engine.dispose()

        self.assertIn("payload_json", columns)
        self.assertIn("content_hash", columns)
        self.assertNotIn("path", columns)
        self.assertNotIn("source_dir", columns)
        self.assertNotIn("source_mtime", columns)
        self.assertIn("candidate_group_id", columns)
        self.assertIn("crawl_task_run_id", columns)
        self.assertIn("crawl_result_id", columns)


if __name__ == "__main__":
    unittest.main()
