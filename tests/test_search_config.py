import tempfile
import textwrap
import unittest
from pathlib import Path

from config.search import SearchRuntimeConfig, load_search_config


class SearchConfigTests(unittest.TestCase):
    def test_default_search_backend_is_browser(self) -> None:
        self.assertEqual(SearchRuntimeConfig().backend, "browser")

    def test_missing_backend_in_yaml_defaults_to_browser(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "search.yaml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    engines:
                      - duckduckgo
                    """
                ).strip(),
                encoding="utf-8",
            )

            config = load_search_config(config_path)

        self.assertEqual(config.backend, "browser")

    def test_loads_search_runtime_settings_from_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "search.yaml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    engines:
                      - duckduckgo
                      - bing
                    max_pages: 4
                    keyword_delay: 5.5
                    engine_request_delay: 2
                    backend: browser
                    headless: false
                    proxy: http://127.0.0.1:7897
                    use_system_proxy: false
                    browser_max_pages: 2
                    """
                ).strip(),
                encoding="utf-8",
            )

            config = load_search_config(config_path)

        self.assertEqual(config.engines, ("duckduckgo", "bing"))
        self.assertEqual(config.max_pages, 4)
        self.assertEqual(config.keyword_delay, 5.5)
        self.assertEqual(config.engine_request_delay, 2.0)
        self.assertEqual(config.backend, "browser")
        self.assertFalse(config.headless)
        self.assertEqual(config.proxy, "http://127.0.0.1:7897")
        self.assertFalse(config.use_system_proxy)
        self.assertEqual(config.browser_max_pages, 2)


if __name__ == "__main__":
    unittest.main()
