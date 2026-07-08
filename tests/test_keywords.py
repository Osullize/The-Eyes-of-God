import tempfile
import textwrap
import unittest
from pathlib import Path

from config.keywords import build_keywords_from_config


class KeywordConfigTests(unittest.TestCase):
    def test_builds_country_industry_synonym_keyword_combinations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "keywords.yaml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    countries:
                      Turkey:
                        terms:
                          - Turkey
                          - Turkiye
                    industries:
                      heat_pump:
                        terms:
                          - heat pump installer
                        synonyms:
                          - HVAC contractor
                    """
                ).strip(),
                encoding="utf-8",
            )

            keywords = build_keywords_from_config(config_path)

        self.assertEqual(
            [item.keyword for item in keywords],
            [
                "heat pump installer Turkey",
                "HVAC contractor Turkey",
                "heat pump installer Turkiye",
                "HVAC contractor Turkiye",
            ],
        )
        self.assertEqual(keywords[0].country, "Turkey")
        self.assertEqual(keywords[0].industry, "heat_pump")
        self.assertEqual(keywords[1].industry_term, "HVAC contractor")


if __name__ == "__main__":
    unittest.main()
