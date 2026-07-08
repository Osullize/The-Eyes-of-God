from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_VUE = ROOT / "frontend" / "src" / "App.vue"
API_TS = ROOT / "frontend" / "src" / "api.ts"
TYPES_TS = ROOT / "frontend" / "src" / "types.ts"


class FrontendRawTablesModuleTests(unittest.TestCase):
    def test_raw_tables_module_is_available_from_sidebar(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn('"rawTables"', source)
        self.assertIn("审计排错", source)
        self.assertIn("审计明细", source)
        self.assertIn("域名主档", source)
        self.assertIn("搜索证据", source)
        self.assertIn("抓取结果", source)
        self.assertNotIn("审计 / 排错，不参与日常流水线", source)
        self.assertNotIn("原始数据表", source)
        self.assertNotIn("审计找官网原始证据，不参与日常流水线", source)
        self.assertNotIn("审计抓官网结构化结果，不参与日常流水线", source)
        self.assertNotIn("直接查看 domains / search_results / crawl_results", source)
        self.assertNotIn("直接查看 domains / search_results / crawl_results / ai_profile_results", source)

    def test_raw_tables_use_dedicated_api_calls(self):
        api_source = API_TS.read_text(encoding="utf-8")
        app_source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("fetchRawDomains", api_source)
        self.assertIn("/raw-tables/domains", api_source)
        self.assertIn("fetchRawSearchResults", api_source)
        self.assertIn("/raw-tables/search-results", api_source)
        self.assertIn("fetchRawCrawlResults", api_source)
        self.assertIn("/raw-tables/crawl-results", api_source)
        self.assertIn("/raw-tables/ai-profile-results", api_source)
        self.assertIn("loadRawTable", app_source)

    def test_raw_tables_define_chinese_columns_for_all_three_tables(self):
        source = APP_VUE.read_text(encoding="utf-8")
        types_source = TYPES_TS.read_text(encoding="utf-8")

        self.assertIn("域名主档", source)
        self.assertIn("搜索证据", source)
        self.assertIn("抓取结果", source)
        self.assertNotIn("域名主表 domains", source)
        self.assertNotIn("找官网结果 search_results", source)
        self.assertNotIn("抓官网结果 crawl_results", source)
        self.assertNotIn("AI画像结果 ai_profile_results", source)
        self.assertIn("关联域名", source)
        self.assertIn("匹配行业词", source)
        self.assertIn("页面分类", source)
        self.assertIn("RawSearchResultRow", types_source)
        self.assertIn("RawCrawlResultRow", types_source)
        self.assertIn("RawAIProfileResultRow", types_source)

    def test_ai_profile_results_have_dedicated_reader_module(self):
        source = APP_VUE.read_text(encoding="utf-8")
        api_source = API_TS.read_text(encoding="utf-8")

        self.assertIn('"aiProfiles"', source)
        self.assertIn("AI画像分析", source)
        self.assertIn("loadAIProfileResults", source)
        self.assertIn("previewAIProfileResult", source)
        self.assertIn("ai-profile-preview-modal", source)
        self.assertIn("上一页目录", source)
        self.assertIn("下一页目录", source)
        self.assertNotIn("查看原始 JSON", source)
        self.assertIn("fetchRawAIProfileResults", api_source)


if __name__ == "__main__":
    unittest.main()
