from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_VUE = ROOT / "frontend" / "src" / "App.vue"
TYPES_TS = ROOT / "frontend" / "src" / "types.ts"
SCHEMAS_PY = ROOT / "api" / "schemas.py"


class FrontendStructuredKeywordTests(unittest.TestCase):
    def test_keyword_group_types_include_structured_search_fields(self):
        source = TYPES_TS.read_text(encoding="utf-8")

        self.assertIn("product_terms: string", source)
        self.assertIn("role_terms: string", source)
        self.assertIn("search_templates: string", source)

    def test_keyword_form_renders_product_role_and_template_fields(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("产品词", source)
        self.assertIn("角色词", source)
        self.assertIn("搜索模板", source)
        self.assertIn("keywordForm.product_terms", source)
        self.assertIn("keywordForm.role_terms", source)
        self.assertIn("keywordForm.search_templates", source)
        self.assertIn("{product} {role} {country}", source)

    def test_api_schema_accepts_structured_search_fields(self):
        source = SCHEMAS_PY.read_text(encoding="utf-8")

        self.assertIn("product_terms: str", source)
        self.assertIn("role_terms: str", source)
        self.assertIn("search_templates: str", source)


if __name__ == "__main__":
    unittest.main()
