import unittest

from crawl.extractors import extract_company_profile
from crawl.extractors import extract_phones


class ExtractorTests(unittest.TestCase):
    def test_extracts_contact_fields_social_links_and_people(self) -> None:
        html = """
            <html>
              <head>
                <title>Acme HVAC - Services</title>
                <meta name="description" content="Industrial heat pump contractor in Istanbul.">
              </head>
              <body>
                <a href="mailto:sales@example.com">sales@example.com</a>
                <p>John Doe - Sales Manager john.doe@example.com</p>
                <p>Tel: +90 (212) 123 45 67</p>
                <p>Address: Main Street No: 5 Istanbul Turkey</p>
                <a href="https://www.linkedin.com/company/acme-hvac">LinkedIn</a>
                <a href="https://www.facebook.com/acmehvac">Facebook</a>
              </body>
            </html>
        """

        profile = extract_company_profile(
            [(html, "https://example.com/contact")],
            fallback_title="Fallback",
            domain="example.com",
            country="Turkey",
        )

        self.assertEqual(profile.company_name, "Acme HVAC")
        self.assertEqual(profile.description, "Industrial heat pump contractor in Istanbul.")
        self.assertIn("sales@example.com", profile.emails)
        self.assertIn("john.doe@example.com", profile.emails)
        self.assertIn("+90 (212) 123 45 67", profile.phones)
        self.assertIn("Main Street No: 5 Istanbul Turkey", profile.possible_address)
        self.assertEqual(profile.social_links["linkedin"], "https://www.linkedin.com/company/acme-hvac")
        self.assertEqual(profile.social_links["facebook"], "https://www.facebook.com/acmehvac")
        self.assertTrue(
            any(contact.name == "John Doe" and contact.title == "Sales Manager" for contact in profile.contacts)
        )

    def test_country_phone_rules_reject_year_ranges(self) -> None:
        phones = extract_phones("Founded 2009 - 2026. Tel: +90 (212) 123 45 67", country="Turkey")

        self.assertEqual(phones, ["+90 (212) 123 45 67"])

    def test_country_phone_rules_require_known_prefix(self) -> None:
        phones = extract_phones("Ref: 1234567890. Tel: 0212 123 45 67", country="Turkey")

        self.assertEqual(phones, ["0212 123 45 67"])


if __name__ == "__main__":
    unittest.main()
