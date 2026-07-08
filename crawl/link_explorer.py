from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


FetchHtml = Callable[[str], tuple[str, str]]


CATEGORY_KEYWORDS = {
    "contact": ["contact", "contact-us", "contacts", "iletisim", "kontakt", "imprint"],
    "about": ["about", "about-us", "company", "hakkimizda", "unternehmen", "who-we-are"],
    "team": ["team", "management", "leadership", "people", "staff", "our-team"],
    "product": ["product", "products", "solution", "solutions", "catalog", "heat-pump"],
    "service": ["service", "services", "support", "installation", "maintenance"],
    "news": ["news", "blog", "press", "media", "article"],
}

CATEGORY_PRIORITY = {
    "home": 0,
    "contact": 1,
    "about": 2,
    "team": 3,
    "product": 4,
    "service": 5,
    "news": 6,
    "other": 20,
}

SKIPPED_SCHEMES = ("mailto:", "tel:", "javascript:", "#")
SKIPPED_EXTENSIONS = re.compile(
    r"\.(pdf|jpg|jpeg|png|gif|webp|zip|rar|doc|docx|xls|xlsx|ppt|pptx)(?:$|\?)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DiscoveredLink:
    url: str
    category: str
    anchor_text: str


@dataclass(frozen=True)
class PageRecord:
    requested_url: str
    final_url: str
    depth: int
    category: str
    html: str


def normalize_domain(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower().strip()
    if ":" in domain:
        domain = domain.split(":", 1)[0]
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def is_same_domain(url: str, domain: str) -> bool:
    link_domain = normalize_domain(url)
    return link_domain == domain or link_domain.endswith("." + domain)


def strip_fragment(url: str) -> str:
    return url.split("#", 1)[0].rstrip("/")


def classify_link(url: str, anchor_text: str) -> str:
    combined = f"{urlparse(url).path} {anchor_text}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in combined for keyword in keywords):
            return category
    return "other"


class LinkExplorer:
    def __init__(self, max_depth: int = 2, max_pages_per_site: int = 12) -> None:
        if max_depth < 0:
            raise ValueError("max_depth must be >= 0")
        if max_pages_per_site < 1:
            raise ValueError("max_pages_per_site must be >= 1")
        self.max_depth = max_depth
        self.max_pages_per_site = max_pages_per_site

    def discover_links(self, base_url: str, html: str, domain: str) -> list[DiscoveredLink]:
        soup = BeautifulSoup(html or "", "html.parser")
        links: list[DiscoveredLink] = []
        seen_urls: set[str] = set()

        for a_tag in soup.find_all("a", href=True):
            href = (a_tag.get("href") or "").strip()
            if not href or href.lower().startswith(SKIPPED_SCHEMES):
                continue

            full_url = strip_fragment(urljoin(base_url, href))
            if not full_url.startswith(("http://", "https://")):
                continue
            if SKIPPED_EXTENSIONS.search(full_url):
                continue
            if not is_same_domain(full_url, domain):
                continue
            if full_url in seen_urls:
                continue

            anchor_text = " ".join(a_tag.get_text(" ", strip=True).split())
            seen_urls.add(full_url)
            links.append(
                DiscoveredLink(
                    url=full_url,
                    category=classify_link(full_url, anchor_text),
                    anchor_text=anchor_text,
                )
            )

        return sorted(links, key=lambda item: (CATEGORY_PRIORITY[item.category], item.url))

    def explore(self, start_url: str, domain: str, fetch_html: FetchHtml) -> list[PageRecord]:
        normalized_domain = domain.lower().removeprefix("www.")
        normalized_start_url = strip_fragment(start_url)
        queue: deque[tuple[str, int, str]] = deque([(normalized_start_url, 0, "home")])
        seen_urls: set[str] = {normalized_start_url}
        final_seen_urls: set[str] = set()
        records: list[PageRecord] = []

        while queue and len(records) < self.max_pages_per_site:
            requested_url, depth, category = queue.popleft()
            requested_url = strip_fragment(requested_url)
            if requested_url in final_seen_urls:
                continue

            try:
                html, final_url = fetch_html(requested_url)
            except Exception:
                continue

            final_url = strip_fragment(final_url or requested_url)
            if final_url in final_seen_urls:
                continue
            final_seen_urls.add(final_url)
            seen_urls.add(final_url)
            records.append(
                PageRecord(
                    requested_url=requested_url,
                    final_url=final_url,
                    depth=depth,
                    category=category,
                    html=html or "",
                )
            )

            if not html or depth >= self.max_depth:
                continue

            for link in self.discover_links(final_url, html, normalized_domain):
                if link.url not in seen_urls and link.url not in final_seen_urls:
                    seen_urls.add(link.url)
                    queue.append((link.url, depth + 1, link.category))

        return records
