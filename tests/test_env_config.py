import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config.env import load_project_env


class EnvConfigTests(unittest.TestCase):
    def test_load_project_env_reads_dotenv_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("DATABASE_URL=sqlite:///fixture.db\nTASK_EXECUTION_MODE=inline\n", encoding="utf-8")

            with patch.dict(os.environ, {}, clear=True):
                loaded = load_project_env(env_file)

                self.assertTrue(loaded)
                self.assertEqual(os.environ["DATABASE_URL"], "sqlite:///fixture.db")
                self.assertEqual(os.environ["TASK_EXECUTION_MODE"], "inline")

    def test_load_project_env_does_not_override_existing_environment_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("DATABASE_URL=sqlite:///file.db\n", encoding="utf-8")

            with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///shell.db"}, clear=True):
                load_project_env(env_file)

                self.assertEqual(os.environ["DATABASE_URL"], "sqlite:///shell.db")


if __name__ == "__main__":
    unittest.main()
