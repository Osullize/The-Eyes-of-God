import unittest

from scripts.run_task import build_parser, params_from_args


class RunTaskCliTests(unittest.TestCase):
    def test_import_existing_data_args_convert_to_handler_params(self) -> None:
        args = build_parser().parse_args(
            [
                "import-existing-data",
                "--database-url",
                "sqlite:///fixture.db",
                "--search-csv",
                "company_websites_france.csv",
                "--crawl-csv",
                "company_info_france.csv",
                "--profile-dir",
                "profile_inputs/france",
                "--no-create-tables",
            ]
        )

        task_type, params = params_from_args(args)

        self.assertEqual(task_type, "import_existing_data")
        self.assertEqual(params["database_url"], "sqlite:///fixture.db")
        self.assertEqual(params["search_csvs"], ["company_websites_france.csv"])
        self.assertEqual(params["crawl_csvs"], ["company_info_france.csv"])
        self.assertEqual(params["profile_dirs"], ["profile_inputs/france"])
        self.assertFalse(params["create_tables"])

    def test_crawl_args_convert_to_handler_params(self) -> None:
        args = build_parser().parse_args(
            [
                "crawl",
                "--input",
                "company_websites_uk.csv",
                "--output",
                "company_info_uk.csv",
                "--state-dir",
                ".crawl_state_uk",
                "--backend",
                "requests",
                "--workers",
                "3",
                "--max-depth",
                "2",
                "--max-pages-per-site",
                "12",
                "--profile-input-dir",
                "profile_inputs/uk",
            ]
        )

        task_type, params = params_from_args(args)

        self.assertEqual(task_type, "crawl")
        self.assertEqual(params["input_file"], "company_websites_uk.csv")
        self.assertEqual(params["workers"], 3)
        self.assertEqual(params["profile_input_dir"], "profile_inputs/uk")


if __name__ == "__main__":
    unittest.main()
