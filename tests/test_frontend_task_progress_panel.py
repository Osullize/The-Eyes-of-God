from pathlib import Path
import unittest


APP_VUE = Path(__file__).resolve().parents[1] / "frontend" / "src" / "App.vue"


class FrontendTaskProgressPanelTests(unittest.TestCase):
    def test_task_console_polls_running_task_runs(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("startTaskRunProgressPolling", source)
        self.assertIn("pollLatestTaskRunProgress", source)
        self.assertIn("fetchTaskRuns({ limit: 1, offset: 0, task_type: taskType, status: \"running\" })", source)
        self.assertIn("fetchTaskRunDetail", source)

    def test_task_console_renders_realtime_progress_panel(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("实时进度", source)
        self.assertIn("activeTaskProgress", source)
        self.assertIn("activeProgressItems", source)
        self.assertIn("progressPercent", source)
        self.assertIn("progress-bar-fill", source)

    def test_running_status_has_chinese_label(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn('normalized === "running"', source)

    def test_task_console_exposes_cancel_action_for_running_task(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("cancelTaskRun", source)
        self.assertIn("cancelActiveTaskRun", source)
        self.assertIn("取消任务", source)
        self.assertIn('normalized === "cancelling"', source)

    def test_refresh_restores_active_task_progress_polling(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("restoreActiveTaskProgressAfterRefresh", source)
        self.assertIn("await restoreActiveTaskProgressAfterRefresh()", source)
        self.assertIn('fetchTaskRuns({ limit: 1, offset: 0, status: "running" })', source)
        self.assertIn("startTaskRunProgressPolling(restoredTaskType)", source)
        self.assertIn("activeModule.value = \"tasks\"", source)


if __name__ == "__main__":
    unittest.main()
