import tempfile
import textwrap
import unittest
from pathlib import Path

from database.models import KeywordGroup
from database.session import create_engine_from_url, create_session_factory
from scripts.import_keyword_groups import import_keyword_groups


class ImportKeywordGroupsScriptTests(unittest.TestCase):
    def test_import_keyword_groups_imports_yaml_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            database_url = f"sqlite:///{base / 'leadgen.db'}"
            yaml_path = base / "keywords_france.yaml"
            yaml_path.write_text(
                textwrap.dedent(
                    """
                    countries:
                      France:
                        terms:
                          - France
                    industries:
                      pool:
                        terms:
                          - pool heat pump
                    """
                ).strip(),
                encoding="utf-8",
            )

            summary = import_keyword_groups(database_url=database_url, paths=[yaml_path])

            engine = create_engine_from_url(database_url)
            Session = create_session_factory(engine)
            with Session() as session:
                groups = session.query(KeywordGroup).all()
            engine.dispose()

        self.assertEqual(summary["imported"], 1)
        self.assertEqual(groups[0].name, "keywords_france")
        self.assertEqual(groups[0].keyword_terms, "pool heat pump")


if __name__ == "__main__":
    unittest.main()
