from pathlib import Path
import unittest


APP_VUE = Path(__file__).resolve().parents[1] / "frontend" / "src" / "App.vue"
API_TS = Path(__file__).resolve().parents[1] / "frontend" / "src" / "api.ts"
TYPES_TS = Path(__file__).resolve().parents[1] / "frontend" / "src" / "types.ts"
STYLE_CSS = Path(__file__).resolve().parents[1] / "frontend" / "src" / "style.css"


class FrontendTaskConsoleDistillTests(unittest.TestCase):
    def test_search_task_keeps_advanced_options_collapsed(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("search-advanced-settings", source)
        self.assertIn("搜索高级设置", source)
        self.assertIn("searchTask.backend", source)
        self.assertIn("searchTask.keyword_delay_seconds", source)
        self.assertIn("searchTask.engine_request_delay_seconds", source)

    def test_search_engine_is_select_with_duckduckgo_default(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("searchEngineOptions", source)
        self.assertIn('engines: "duckduckgo"', source)
        self.assertIn('value: "duckduckgo"', source)
        self.assertIn('value: "bing"', source)
        self.assertIn('value: "duckduckgo,bing"', source)
        self.assertIn('<select v-model="searchTask.engines">', source)
        self.assertNotIn('<input v-model="searchTask.engines" type="text" />', source)

    def test_crawl_task_has_preset_and_advanced_settings(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("crawlPresetOptions", source)
        self.assertIn("applyCrawlPreset", source)
        self.assertIn("抓取预设", source)
        self.assertIn("crawl-advanced-settings", source)
        self.assertIn("抓取高级设置", source)
        self.assertIn("代理与浏览器", source)
        self.assertIn("重试退避", source)

    def test_crawl_daily_decisions_are_marked_as_primary(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("task-form daily-task-form crawl-daily-form", source)
        self.assertIn("candidate-source-summary", source)
        self.assertIn("task-preset-strip", source)
        self.assertIn("搜索高级设置", source)
        self.assertIn("抓取高级设置", source)

    def test_import_task_is_removed_from_daily_console(self):
        app_source = APP_VUE.read_text(encoding="utf-8")
        api_source = API_TS.read_text(encoding="utf-8")
        types_source = TYPES_TS.read_text(encoding="utf-8")
        style_source = STYLE_CSS.read_text(encoding="utf-8")

        self.assertIn("搜索、抓取、画像", app_source)
        self.assertNotIn("{ label: \"入库\"", app_source)
        self.assertNotIn("UploadCloud", app_source)
        self.assertNotIn("importTask", app_source)
        self.assertNotIn("startImportTask", api_source)
        self.assertNotIn("ImportTaskRequest", types_source)
        self.assertNotIn("import-form", style_source)

    def test_raw_tables_are_positioned_as_audit_module(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("审计排错", source)
        self.assertIn("审计 / 排错", source)
        self.assertIn("审计明细", source)
        self.assertNotIn("直接查看 domains / search_results / crawl_results", source)


if __name__ == "__main__":
    unittest.main()
