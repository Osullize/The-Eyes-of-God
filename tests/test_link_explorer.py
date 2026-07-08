import unittest

from crawl.link_explorer import LinkExplorer


class LinkExplorerTests(unittest.TestCase):
    def test_explores_same_domain_links_by_depth_and_page_limit(self) -> None:
        pages = {
            "https://example.com": """
                <a href="/contact">Contact</a>
                <a href="/about">About us</a>
                <a href="/products/heat-pumps">Products</a>
                <a href="https://external.example/contact">External</a>
            """,
            "https://example.com/about": """
                <a href="/team">Team</a>
            """,
            "https://example.com/contact": "<p>Email us</p>",
            "https://example.com/products/heat-pumps": "<p>Product details</p>",
            "https://example.com/team": "<p>Team details</p>",
        }

        def fetcher(url: str) -> tuple[str, str]:
            return pages[url], url

        explorer = LinkExplorer(max_depth=2, max_pages_per_site=5)
        records = explorer.explore("https://example.com", "example.com", fetcher)

        urls = {record.final_url for record in records}
        categories = {record.final_url: record.category for record in records}

        self.assertEqual(len(records), 5)
        self.assertIn("https://example.com/contact", urls)
        self.assertIn("https://example.com/team", urls)
        self.assertNotIn("https://external.example/contact", urls)
        self.assertEqual(categories["https://example.com/contact"], "contact")
        self.assertEqual(categories["https://example.com/about"], "about")
        self.assertEqual(categories["https://example.com/team"], "team")
        self.assertEqual(categories["https://example.com/products/heat-pumps"], "product")

    def test_marks_queued_and_redirect_final_urls_seen(self) -> None:
        pages = {
            "https://example.com": """
                <a href="/z-source">Contact A</a>
                <a href="/zz-final">Contact final</a>
                <a href="/z-source#section">Contact A duplicate</a>
            """,
            "https://example.com/z-source": ("<p>Contact</p>", "https://example.com/zz-final"),
            "https://example.com/zz-final": ("<p>Contact</p>", "https://example.com/zz-final"),
        }
        fetched: list[str] = []

        def fetcher(url: str) -> tuple[str, str]:
            fetched.append(url)
            page = pages[url]
            if isinstance(page, tuple):
                return page
            return page, url

        explorer = LinkExplorer(max_depth=1, max_pages_per_site=10)
        records = explorer.explore("https://example.com", "example.com", fetcher)

        self.assertEqual([record.final_url for record in records], ["https://example.com", "https://example.com/zz-final"])
        self.assertEqual(fetched.count("https://example.com/z-source"), 1)
        self.assertNotIn("https://example.com/zz-final", fetched)


if __name__ == "__main__":
    unittest.main()
