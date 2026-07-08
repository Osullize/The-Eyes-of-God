import csv
import tempfile
import unittest
from pathlib import Path

from pipeline.csv_writer import append_deduped_rows


class CsvWriterTests(unittest.TestCase):
    def test_appends_new_rows_and_updates_duplicate_by_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "companies.csv"
            with output.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["domain", "emails", "status"])
                writer.writeheader()
                writer.writerow({"domain": "example.com", "emails": "old@example.com", "status": "old"})

            append_deduped_rows(
                output,
                [
                    {"domain": "example.com", "emails": "new@example.com", "status": "success"},
                    {"domain": "vendor.example", "emails": "sales@vendor.example", "status": "success"},
                ],
                fieldnames=["domain", "emails", "status"],
                key_field="domain",
            )

            with output.open("r", encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["domain"], "example.com")
        self.assertEqual(rows[0]["emails"], "new@example.com")
        self.assertEqual(rows[1]["domain"], "vendor.example")


if __name__ == "__main__":
    unittest.main()
