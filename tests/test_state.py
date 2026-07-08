import tempfile
import unittest
from pathlib import Path

from pipeline.state import CrawlState


class CrawlStateTests(unittest.TestCase):
    def test_persists_completed_domains_and_failed_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state = CrawlState(Path(temp_dir))
            state.mark_completed("example.com")
            state.mark_failed("broken.example", "timeout")

            reloaded = CrawlState(Path(temp_dir))

        self.assertTrue(reloaded.is_completed("example.com"))
        self.assertEqual(reloaded.failed_domains(), ["broken.example"])
        self.assertEqual(reloaded.failure_reason("broken.example"), "timeout")

    def test_mark_completed_removes_domain_from_failed_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state = CrawlState(Path(temp_dir))
            state.mark_failed("example.com", "timeout")
            state.mark_completed("example.com")
            reloaded = CrawlState(Path(temp_dir))

        self.assertTrue(reloaded.is_completed("example.com"))
        self.assertEqual(reloaded.failed_domains(), [])


if __name__ == "__main__":
    unittest.main()
