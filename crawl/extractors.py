from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urljoin

from bs4 import BeautifulSoup


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+|00)?\d[\d\s()./-]{7,}\d")
PERSON_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*[-–|,]\s*"
    r"([A-Za-z][A-Za-z\s/&]{2,80}?)\s+"
    r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
)

ADDRESS_KEYWORDS = [
    "address",
    "location",
    "office",
    "headquarters",
    "factory",
    "warehouse",
    "adres",
    "anschrift",
    "street",
    "road",
    "cad",
    "mah",
    "sok",
    "no:",
    "istanbul",
    "ankara",
    "izmir",
    "dubai",
    "abu dhabi",
    "berlin",
    "munich",
]

COUNTRY_PHONE_RULES = {
    "turkey": {
        "country_prefixes": ("90",),
        "country_min": 12,
        "country_max": 12,
        "local_prefixes": ("0",),
        "local_min": 11,
        "local_max": 11,
    },
    "germany": {
        "country_prefixes": ("49",),
        "country_min": 8,
        "country_max": 15,
        "local_prefixes": ("0",),
        "local_min": 8,
        "local_max": 15,
    },
    "united arab emirates": {
        "country_prefixes": ("971",),
        "country_min": 11,
        "country_max": 12,
        "local_prefixes": ("0",),
        "local_min": 9,
        "local_max": 10,
    },
    "uae": {
        "country_prefixes": ("971",),
        "country_min": 11,
        "country_max": 12,
        "local_prefixes": ("0",),
        "local_min": 9,
        "local_max": 10,
    },
}


@dataclass(frozen=True)
class ContactPerson:
    name: str
    title: str
    email: str


@dataclass
class CompanyProfile:
    company_name: str
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    possible_address: str = ""
    description: str = ""
    social_links: dict[str, str] = field(default_factory=dict)
    contacts: list[ContactPerson] = field(default_factory=list)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or " ").strip()


def extract_emails(text: str) -> list[str]:
    emails: list[str] = []
    for match in EMAIL_RE.findall(text or ""):
        email = match.strip(".,;:)]}>'\"").lower()
        if email.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
            continue
        if email not in emails:
            emails.append(email)
    return emails


def _phone_digits(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("00"):
        digits = digits[2:]
    return digits


def _phone_matches_country(digits: str, country: str | None) -> bool:
    if not country:
        return 8 <= len(digits) <= 18

    rule = COUNTRY_PHONE_RULES.get(country.strip().lower())
    if not rule:
        return 8 <= len(digits) <= 18

    if digits.startswith(rule["country_prefixes"]) and rule["country_min"] <= len(digits) <= rule["country_max"]:
        return True

    if digits.startswith(rule["local_prefixes"]) and rule["local_min"] <= len(digits) <= rule["local_max"]:
        return True

    return False


def extract_phones(text: str, country: str | None = None) -> list[str]:
    phones: list[str] = []
    for match in PHONE_RE.findall(text or ""):
        phone = clean_text(match.strip(".,;:)]}"))
        digits = _phone_digits(phone)
        if not _phone_matches_country(digits, country):
            continue
        if phone not in phones:
            phones.append(phone)
    return phones[:20]


def extract_company_name(soup: BeautifulSoup, fallback_title: str, domain: str) -> str:
    if soup.title and soup.title.string:
        title = clean_text(soup.title.string)
        title = re.split(r"[|\-–—]", title)[0].strip()
        if title:
            return title[:120]

    og_site_name = soup.find("meta", property="og:site_name")
    if og_site_name and og_site_name.get("content"):
        return clean_text(og_site_name["content"])[:120]

    return (fallback_title or domain)[:120]


def extract_description(soup: BeautifulSoup, page_text: str) -> str:
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return clean_text(meta["content"])[:500]

    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        return clean_text(og_desc["content"])[:500]

    return clean_text(page_text)[:500]


def extract_possible_address(text: str) -> str:
    lines = [clean_text(line) for line in (text or "").splitlines() if clean_text(line)]

    for index, line in enumerate(lines):
        lower = line.lower()
        if any(keyword in lower for keyword in ADDRESS_KEYWORDS):
            nearby = lines[index:index + 4]
            return " | ".join(nearby)[:500]

    return ""


def extract_social_links(soup: BeautifulSoup, base_url: str) -> dict[str, str]:
    social_hosts = {
        "linkedin": "linkedin.com",
        "facebook": "facebook.com",
        "instagram": "instagram.com",
    }
    links: dict[str, str] = {}

    for a_tag in soup.find_all("a", href=True):
        href = urljoin(base_url, a_tag.get("href", "").strip())
        lower = href.lower()
        for name, host in social_hosts.items():
            if host in lower and name not in links:
                links[name] = href.split("#", 1)[0]

    return links


def extract_contacts(text: str) -> list[ContactPerson]:
    contacts: list[ContactPerson] = []
    seen_emails: set[str] = set()

    for match in PERSON_RE.finditer(text or ""):
        name = clean_text(match.group(1))
        title = clean_text(match.group(2).strip("-–|, "))
        email = match.group(3).lower()
        if email in seen_emails:
            continue
        seen_emails.add(email)
        contacts.append(ContactPerson(name=name, title=title, email=email))

    return contacts


def extract_company_profile(
    pages: list[tuple[str, str]],
    fallback_title: str,
    domain: str,
    country: str | None = None,
) -> CompanyProfile:
    first_soup: BeautifulSoup | None = None
    first_text = ""
    all_text_parts: list[str] = []
    emails: list[str] = []
    phones: list[str] = []
    contacts: list[ContactPerson] = []
    social_links: dict[str, str] = {}

    for html, page_url in pages:
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()

        page_text = soup.get_text("\n", strip=True)
        if first_soup is None:
            first_soup = soup
            first_text = page_text

        combined = html + "\n" + page_text
        all_text_parts.append(page_text)

        for email in extract_emails(combined):
            if email not in emails:
                emails.append(email)

        for phone in extract_phones(page_text, country=country):
            if phone not in phones:
                phones.append(phone)

        for name, href in extract_social_links(soup, page_url).items():
            social_links.setdefault(name, href)

        seen_contact_emails = {contact.email for contact in contacts}
        for contact in extract_contacts(page_text):
            if contact.email not in seen_contact_emails:
                contacts.append(contact)
                seen_contact_emails.add(contact.email)

    full_text = "\n".join(all_text_parts)
    if first_soup is not None:
        company_name = extract_company_name(first_soup, fallback_title, domain)
        description = extract_description(first_soup, first_text)
    else:
        company_name = fallback_title or domain
        description = ""

    return CompanyProfile(
        company_name=company_name,
        emails=emails[:20],
        phones=phones[:20],
        possible_address=extract_possible_address(full_text),
        description=description,
        social_links=social_links,
        contacts=contacts,
    )
