from pathlib import Path
import unittest


APP_VUE = Path(__file__).resolve().parents[1] / "frontend" / "src" / "App.vue"


class FrontendCrawlFormStateTests(unittest.TestCase):
    def test_crawl_candidate_filters_are_disabled_when_group_is_selected(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("isCandidateFilterDisabled", source)
        self.assertIn(":disabled=\"isCandidateFilterDisabled\"", source)
        self.assertIn(":class=\"{ disabled: isCandidateFilterDisabled }\"", source)

    def test_browser_only_fields_are_disabled_in_requests_mode(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("isBrowserMode", source)
        self.assertIn(":disabled=\"!isBrowserMode\"", source)
        self.assertIn(":class=\"{ disabled: !isBrowserMode }\"", source)

    def test_requests_only_fields_are_disabled_in_browser_mode(self):
        source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("isRequestsMode", source)
        self.assertIn(":disabled=\"!isRequestsMode\"", source)
        self.assertIn(":class=\"{ disabled: !isRequestsMode }\"", source)


if __name__ == "__main__":
    unittest.main()
