from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_VUE = ROOT / "frontend" / "src" / "App.vue"
STYLE_CSS = ROOT / "frontend" / "src" / "style.css"


class FrontendVisualRedesignTests(unittest.TestCase):
    def test_console_uses_distinct_heat_pump_command_tokens(self):
        source = STYLE_CSS.read_text(encoding="utf-8")

        self.assertIn("gpt-taste console redesign", source)
        self.assertIn("--ink-950", source)
        self.assertIn("--accent-teal", source)
        self.assertIn("--accent-amber", source)
        self.assertIn('Geist, "Cabinet Grotesk"', source)
        self.assertNotIn("Inter, ui-sans-serif", source)

    def test_sidebar_is_redesigned_as_command_rail(self):
        source = STYLE_CSS.read_text(encoding="utf-8")
        app_source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn('class="app-shell console-redesign"', app_source)
        self.assertIn("sidebarCollapsed", app_source)
        self.assertIn("sidebar-toggle", app_source)
        self.assertIn("PanelLeftClose", app_source)
        self.assertIn("PanelLeftOpen", app_source)
        self.assertIn("grid-template-columns: 292px minmax(0, 1fr)", source)
        self.assertIn("grid-template-columns: 76px minmax(0, 1fr)", source)
        self.assertIn(".sidebar::before", source)
        self.assertIn(".sidebar-nav button.active::before", source)
        self.assertIn(".console-redesign.sidebar-collapsed .sidebar-nav span", source)

    def test_metrics_use_compact_top_status_density(self):
        source = STYLE_CSS.read_text(encoding="utf-8")
        app_source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("module-overview", app_source)
        self.assertIn("topbar-actions", app_source)
        self.assertNotIn("后端 {{ apiBaseUrl }}", app_source)
        self.assertIn("grid-auto-flow: dense", source)
        self.assertIn("repeat(4, minmax(116px, 1fr))", source)
        self.assertIn(".metric-card:nth-child(1)", source)
        self.assertIn("height: 44px", source)
        self.assertIn("min-height: 44px", source)

    def test_tables_and_ai_reader_have_premium_console_treatment(self):
        source = STYLE_CSS.read_text(encoding="utf-8")

        self.assertIn(".table-wrap table", source)
        self.assertIn(".table-wrap thead th", source)
        self.assertIn("position: sticky", source)
        self.assertIn(".ai-profile-page::before", source)
        self.assertIn(".ai-score-strip", source)
        self.assertIn(".task-progress-panel::before", source)


if __name__ == "__main__":
    unittest.main()
