from __future__ import annotations

import re
from urllib.parse import parse_qs, unquote, urlparse


BLOCKED_DOMAINS = {
    "google.com",
    "google.com.hk",
    "maps.google.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "wikipedia.org",
    "yelp.com",
    "tripadvisor.com",
    "yellowpages.com",
    "kompass.com",
    "europages.com",
    "made-in-china.com",
    "alibaba.com",
    "amazon.com",
    "ebay.com",
    "pinterest.com",
    "reddit.com",
    "indeed.com",
    "glassdoor.com",
    "duckduckgo.com",
    "bing.com",
}

BLOCKED_DOMAIN_KEYWORDS = [
    "facebook.",
    "instagram.",
    "linkedin.",
    "youtube.",
    "google.",
    "yelp.",
    "yellowpages.",
    "kompass.",
    "europages.",
    "alibaba.",
    "made-in-china.",
    "amazon.",
    "reddit.",
    "pinterest.",
    "duckduckgo.",
    "bing.",
]

FILE_EXTENSION_PATTERN = re.compile(
    r"\.(pdf|jpg|jpeg|png|gif|webp|zip|rar|doc|docx|xls|xlsx|ppt|pptx)(?:$|\?)",
    re.IGNORECASE,
)


def normalize_domain(url: str) -> str:
    parsed = urlparse((url or "").strip())
    domain = parsed.netloc.lower().strip()
    if "@" in domain:
        domain = domain.rsplit("@", 1)[-1]
    if ":" in domain:
        domain = domain.split(":", 1)[0]
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def clean_result_url(raw_url: str) -> str:
    if not raw_url:
        return ""

    raw_url = unquote(raw_url)
    parsed = urlparse(raw_url)

    if "duckduckgo.com" in parsed.netloc and parsed.query:
        query = parse_qs(parsed.query)
        if query.get("uddg"):
            return query["uddg"][0]

    if "bing.com" in parsed.netloc and parsed.path.startswith("/ck/") and parsed.query:
        query = parse_qs(parsed.query)
        if query.get("u"):
            return query["u"][0]

    if raw_url.startswith("//"):
        return "https:" + raw_url

    return raw_url


def is_valid_company_site(url: str) -> bool:
    if not url.startswith(("http://", "https://")):
        return False

    domain = normalize_domain(url)
    if not domain or "." not in domain:
        return False
    if domain in BLOCKED_DOMAINS:
        return False
    if any(keyword in domain for keyword in BLOCKED_DOMAIN_KEYWORDS):
        return False
    if FILE_EXTENSION_PATTERN.search(url):
        return False

    return True
