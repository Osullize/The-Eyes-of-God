import tempfile
import unittest
from pathlib import Path

from pipeline.search_state import SearchState


class SearchStateTests(unittest.TestCase):
    def test_persists_completed_and_failed_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state = SearchState(Path(temp_dir))
            state.mark_completed("heat pump Turkey")
            state.mark_failed("HVAC Turkey", "blocked")
            reloaded = SearchState(Path(temp_dir))

        self.assertTrue(reloaded.is_completed("heat pump Turkey"))
        self.assertEqual(reloaded.failed_keywords(), ["HVAC Turkey"])
        self.assertEqual(reloaded.failure_reason("HVAC Turkey"), "blocked")


if __name__ == "__main__":
    unittest.main()
