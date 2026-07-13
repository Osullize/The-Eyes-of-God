from pathlib import Path
import unittest


APP_VUE = Path(__file__).resolve().parents[1] / "frontend" / "src" / "App.vue"
API_TS = Path(__file__).resolve().parents[1] / "frontend" / "src" / "api.ts"
TYPES_TS = Path(__file__).resolve().parents[1] / "frontend" / "src" / "types.ts"


class FrontendTaskResultsModuleTests(unittest.TestCase):
    def test_task_center_links_to_existing_crawl_result_view_without_export_button(self):
        source = APP_VUE.read_text(encoding="utf-8")
        task_center_start = source.index("activeModule === 'taskCenter'")
        task_center_end = source.index("activeModule === 'library'")
        task_center_block = source[task_center_start:task_center_end]

        self.assertIn("查看结果", task_center_block)
        self.assertIn("openTaskRunResults", task_center_block)
        self.assertNotIn("导出XLSX", task_center_block)
        self.assertNotIn("activeModule === 'taskResults'", source)
        self.assertNotIn('{ label: "任务结果"', source)

    def test_open_task_results_jumps_to_raw_crawl_results_with_task_marker(self):
        source = APP_VUE.read_text(encoding="utf-8")
        function_start = source.index("async function openTaskRunResults")
        function_end = source.index("async function loadCompanyLibrary(resetPage", function_start)
        function_block = source[function_start:function_end]

        self.assertIn('selectedRawTable.value = "crawl_results"', function_block)
        self.assertIn("rawTableFilters.q = `task:crawl:${taskRun.id}`", function_block)
        self.assertIn('activeModule.value = "rawTables"', function_block)
        self.assertIn("await loadRawTable(true)", function_block)
        self.assertIn("selectCurrentPageRawCrawlResults()", function_block)
        self.assertIn('rawTableFilters.country = ""', function_block)
        self.assertIn('rawTableFilters.status = ""', function_block)
        self.assertIn('rawTableFilters.engine = ""', function_block)
        self.assertIn('rawTableFilters.keyword = ""', function_block)

    def test_existing_raw_crawl_result_view_contains_selection_and_xlsx_export(self):
        source = APP_VUE.read_text(encoding="utf-8")
        raw_view_start = source.index("activeModule === 'rawTables'")
        raw_view_end = source.index("activeModule === 'aiProfiles'")
        raw_view_block = source[raw_view_start:raw_view_end]

        self.assertIn("抓取结果", source)
        self.assertIn("导出XLSX", raw_view_block)
        self.assertIn('v-if="selectedRawTable === \'crawl_results\'"', raw_view_block)
        self.assertIn("selectedRawCrawlResultCount === 0", raw_view_block)
        self.assertIn("allCurrentPageRawCrawlResultsSelected", raw_view_block)
        self.assertIn("toggleCurrentPageRawCrawlResults", raw_view_block)
        self.assertIn("isRawCrawlResultSelected(row)", raw_view_block)
        self.assertIn("toggleRawCrawlResultSelection(row)", raw_view_block)
        self.assertIn("exportCurrentCrawlTaskResultsXlsx", raw_view_block)
        self.assertIn("exportSelectedRawCrawlResultsXlsx", source)
        self.assertNotIn("fetchTaskRunResults", source)

    def test_existing_raw_crawl_result_view_can_change_page_size(self):
        source = APP_VUE.read_text(encoding="utf-8")
        raw_view_start = source.index("activeModule === 'rawTables'")
        raw_view_end = source.index("activeModule === 'aiProfiles'")
        raw_view_block = source[raw_view_start:raw_view_end]

        self.assertIn("最大显示条数", raw_view_block)
        self.assertIn("rawTablePageSizeOptions", raw_view_block)
        self.assertIn("setRawTablePageSize", raw_view_block)
        self.assertIn("const rawTablePageSizeOptions = [100, 300, 500]", source)
        self.assertIn("limit: 100", source[source.index("const rawTableFilters = reactive"):source.index("const aiProfileFilters = reactive")])

    def test_task_result_api_client_keeps_selected_xlsx_export_only(self):
        api_source = API_TS.read_text(encoding="utf-8")
        types_source = TYPES_TS.read_text(encoding="utf-8")

        self.assertIn("exportSelectedRawCrawlResultsXlsx", api_source)
        self.assertIn("/raw-tables/crawl-results/export.xlsx", api_source)
        self.assertNotIn("fetchTaskRunResults", api_source)
        self.assertNotIn("TaskRunResultsResponse", types_source)
        self.assertNotIn("CrawlTaskResultRow", types_source)


if __name__ == "__main__":
    unittest.main()
