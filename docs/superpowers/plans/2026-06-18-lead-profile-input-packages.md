# Lead Profile Input Packages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate per-company JSON input packages and a reusable analysis prompt so a separate Codex can analyze heat-pump B2B lead profiles from crawled website evidence.

**Architecture:** Add a pure `profile_analysis` packaging module that converts crawl records and extracted contacts into the approved input schema. Wire `run_crawl.py` to optionally write one JSON package per successfully crawled company, without calling AI or changing the existing CSV workflow. Add a prompt handoff document for the separate profile-analysis Codex.

**Tech Stack:** Python 3, `unittest`, `BeautifulSoup`, standard-library `json`, existing `run_crawl.py`, existing crawl/extractor dataclasses.

---

## Scope

This first implementation builds the handoff layer only:

- Create profile-analysis input JSON packages.
- Preserve company metadata, search-source metadata, contacts, page URLs, page categories, visible page text, and crawl metadata.
- Add optional `run_crawl.py` CLI flags for package export.
- Add a reusable prompt document for the separate analysis Codex.

This plan does not call an AI API, does not score leads in this project, and does not generate marketing emails.

## File Structure

- Create `profile_analysis/__init__.py`: package marker.
- Create `profile_analysis/input_package.py`: pure functions for text extraction, page ordering, package building, and JSON writing.
- Create `tests/test_profile_input_package.py`: unit tests for the package builder.
- Modify `run_crawl.py`: optional profile input package export after each successful company crawl.
- Modify `tests/test_run_crawl.py`: integration tests for CLI flags and package export.
- Create `docs/profile-analysis-agent-prompt.md`: copy-ready prompt for the separate profile-analysis Codex.
- Modify `README.md`: document the new package export command and output directory.
- Modify `AI_WORKLOG.md`: record implementation decisions and verification.

## Task 1: Add Pure Profile Input Package Builder

**Files:**
- Create: `profile_analysis/__init__.py`
- Create: `profile_analysis/input_package.py`
- Test: `tests/test_profile_input_package.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_profile_input_package.py`:

```python
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from profile_analysis.input_package import (
    build_profile_input_package,
    safe_package_filename,
    visible_text_from_html,
    write_profile_input_package,
)


class ProfileInputPackageTests(unittest.TestCase):
    def test_visible_text_removes_scripts_styles_and_normalizes_whitespace(self) -> None:
        html = """
            <html>
              <head><style>.hidden { display: none; }</style></head>
              <body>
                <script>window.noisy = true;</script>
                <h1>Heat Pump Services</h1>
                <p>Installation   and maintenance</p>
              </body>
            </html>
        """

        text = visible_text_from_html(html)

        self.assertEqual(text, "Heat Pump Services Installation and maintenance")

    def test_safe_package_filename_normalizes_domain(self) -> None:
        self.assertEqual(safe_package_filename("www.Acme Example.com"), "acme-example.com.json")
        self.assertEqual(safe_package_filename(""), "unknown.json")

    def test_build_profile_input_package_preserves_metadata_contacts_and_priority_pages(self) -> None:
        company = {
            "keyword": "HVAC contractor Germany",
            "title": "Fallback Acme",
            "website": "https://acme.example",
            "domain": "acme.example",
            "country": "Germany",
            "industry": "hvac",
            "matched_keywords": "HVAC contractor Germany; heat pump installer Germany",
            "matched_countries": "Germany",
            "matched_industries": "hvac; heat_pump",
            "matched_industry_terms": "HVAC contractor; heat pump installer",
        }
        profile = SimpleNamespace(
            company_name="Acme HVAC",
            emails=["sales@acme.example"],
            phones=["+49 30 123456"],
            social_links={"linkedin": "https://linkedin.com/company/acme"},
            contacts=[
                SimpleNamespace(
                    name="Jane Smith",
                    title="Sales Manager",
                    email="jane@acme.example",
                )
            ],
        )
        records = [
            SimpleNamespace(
                final_url="https://acme.example/blog",
                category="news",
                html="<html><body><p>Company news</p></body></html>",
            ),
            SimpleNamespace(
                final_url="https://acme.example/services",
                category="service",
                html="""
                    <html>
                      <head><title>Services</title></head>
                      <body><p>Heat pump installation and HVAC project services for commercial buildings.</p></body>
                    </html>
                """,
            ),
        ]

        package = build_profile_input_package(
            company=company,
            profile=profile,
            records=records,
            status="success",
            errors=[],
            crawl_time="2026-06-18T10:00:00+08:00",
            max_pages=1,
            page_char_limit=28,
        )

        self.assertEqual(package["schema_version"], "1.0")
        self.assertEqual(package["company"]["domain"], "acme.example")
        self.assertEqual(package["company"]["company_name"], "Acme HVAC")
        self.assertEqual(package["company"]["source_keyword"], "HVAC contractor Germany")
        self.assertEqual(package["contacts"]["emails"], ["sales@acme.example"])
        self.assertEqual(package["contacts"]["people"][0]["email"], "jane@acme.example")
        self.assertEqual(len(package["pages"]), 1)
        self.assertEqual(package["pages"][0]["category"], "service")
        self.assertEqual(package["pages"][0]["title"], "Services")
        self.assertEqual(package["pages"][0]["text"], "Heat pump installation and")
        self.assertEqual(package["crawl_metadata"]["crawled_pages"], 2)
        self.assertEqual(package["crawl_metadata"]["status"], "success")

    def test_write_profile_input_package_uses_domain_filename(self) -> None:
        package = {
            "schema_version": "1.0",
            "company": {"domain": "acme.example"},
            "contacts": {},
            "pages": [],
            "crawl_metadata": {"crawled_pages": 0, "status": "success", "errors": [], "crawl_time": ""},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = write_profile_input_package(package, Path(temp_dir))
            content = path.read_text(encoding="utf-8")

        self.assertEqual(path.name, "acme.example.json")
        self.assertIn('"schema_version": "1.0"', content)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m unittest tests/test_profile_input_package.py
```

Expected: FAIL with `ModuleNotFoundError: No module named 'profile_analysis'`.

- [ ] **Step 3: Create package marker**

Create `profile_analysis/__init__.py`:

```python
"""Profile-analysis handoff package builders."""
```

- [ ] **Step 4: Implement `profile_analysis/input_package.py`**

Create `profile_analysis/input_package.py`:

```python
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from bs4 import BeautifulSoup


SCHEMA_VERSION = "1.0"

PAGE_CATEGORY_PRIORITY = {
    "home": 0,
    "product": 1,
    "service": 2,
    "about": 3,
    "contact": 4,
    "team": 5,
    "news": 6,
    "other": 20,
}


def _value(source: Any, key: str, default: str = "") -> str:
    if isinstance(source, Mapping):
        value = source.get(key, default)
    else:
        value = getattr(source, key, default)
    return str(value or "")


def _list_value(source: Any, key: str) -> list[str]:
    value = getattr(source, key, [])
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []


def _dict_value(source: Any, key: str) -> dict[str, str]:
    value = getattr(source, key, {})
    if isinstance(value, dict):
        return {str(item_key): str(item_value) for item_key, item_value in value.items() if str(item_value)}
    return {}


def _trim_text(text: str, limit: int) -> str:
    if limit < 1:
        raise ValueError("page_char_limit must be >= 1")
    return (text or "")[:limit].rstrip()


def visible_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def page_title_from_html(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    if soup.title and soup.title.string:
        return re.sub(r"\s+", " ", soup.title.string).strip()
    return ""


def safe_package_filename(domain: str) -> str:
    value = (domain or "").strip().lower()
    if value.startswith("www."):
        value = value[4:]
    value = re.sub(r"[^a-z0-9.-]+", "-", value).strip(".-")
    return f"{value or 'unknown'}.json"


def _contact_people(profile: Any) -> list[dict[str, str]]:
    people: list[dict[str, str]] = []
    for contact in getattr(profile, "contacts", []):
        person = {
            "name": _value(contact, "name"),
            "title": _value(contact, "title"),
            "email": _value(contact, "email"),
        }
        if person["name"] or person["title"] or person["email"]:
            people.append(person)
    return people


def _page_sort_key(record: Any) -> tuple[int, str]:
    category = _value(record, "category", "other") or "other"
    return (PAGE_CATEGORY_PRIORITY.get(category, PAGE_CATEGORY_PRIORITY["other"]), _value(record, "final_url"))


def _page_payloads(records: list[Any], max_pages: int, page_char_limit: int) -> list[dict[str, str]]:
    if max_pages < 1:
        raise ValueError("max_pages must be >= 1")

    pages: list[dict[str, str]] = []
    for record in sorted(records, key=_page_sort_key):
        html = _value(record, "html")
        if not html:
            continue
        text = _trim_text(visible_text_from_html(html), page_char_limit)
        if not text:
            continue
        pages.append(
            {
                "url": _value(record, "final_url") or _value(record, "requested_url"),
                "category": _value(record, "category", "other") or "other",
                "title": page_title_from_html(html),
                "text": text,
            }
        )
        if len(pages) >= max_pages:
            break
    return pages


def build_profile_input_package(
    company: Any,
    profile: Any,
    records: list[Any],
    status: str,
    errors: list[str] | None = None,
    crawl_time: str | None = None,
    max_pages: int = 12,
    page_char_limit: int = 8000,
) -> dict[str, Any]:
    company_name = _value(profile, "company_name") or _value(company, "title") or _value(company, "domain")
    package = {
        "schema_version": SCHEMA_VERSION,
        "company": {
            "domain": _value(company, "domain").lower(),
            "website": _value(company, "website"),
            "company_name": company_name,
            "country": _value(company, "country"),
            "industry": _value(company, "industry"),
            "source_keyword": _value(company, "keyword"),
            "matched_keywords": _value(company, "matched_keywords") or _value(company, "keyword"),
            "matched_countries": _value(company, "matched_countries") or _value(company, "country"),
            "matched_industries": _value(company, "matched_industries") or _value(company, "industry"),
            "matched_industry_terms": _value(company, "matched_industry_terms"),
        },
        "contacts": {
            "emails": _list_value(profile, "emails"),
            "phones": _list_value(profile, "phones"),
            "social_links": _dict_value(profile, "social_links"),
            "people": _contact_people(profile),
        },
        "pages": _page_payloads(records, max_pages=max_pages, page_char_limit=page_char_limit),
        "crawl_metadata": {
            "crawled_pages": len([record for record in records if _value(record, "html")]),
            "status": status,
            "errors": errors or [],
            "crawl_time": crawl_time or datetime.now(timezone.utc).isoformat(),
        },
    }
    return package


def write_profile_input_package(package: dict[str, Any], output_dir: str | Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    domain = str(package.get("company", {}).get("domain", ""))
    file_path = output_path / safe_package_filename(domain)
    file_path.write_text(
        json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return file_path
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
python -m unittest tests/test_profile_input_package.py
```

Expected: PASS, 4 tests.

- [ ] **Step 6: Commit**

```bash
git add profile_analysis/__init__.py profile_analysis/input_package.py tests/test_profile_input_package.py
git commit -m "feat: add profile input package builder"
```

## Task 2: Add Optional Package Export To `run_crawl.py`

**Files:**
- Modify: `run_crawl.py`
- Test: `tests/test_run_crawl.py`

- [ ] **Step 1: Add failing integration tests**

Modify the imports at the top of `tests/test_run_crawl.py`:

```python
import csv
import json
import tempfile
import unittest
from pathlib import Path
```

Add assertions to `test_cli_exposes_depth_page_and_concurrency_controls`:

```python
                "--profile-input-dir",
                "profile_inputs",
                "--profile-page-char-limit",
                "1200",
```

Then add these assertions in that test:

```python
        self.assertEqual(args.profile_input_dir, "profile_inputs")
        self.assertEqual(args.profile_page_char_limit, 1200)
```

Add a new test method to `RunCrawlTests`:

```python
    def test_run_crawl_writes_profile_input_package_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            input_file = base / "company_websites.csv"
            output_file = base / "company_info.csv"
            state_dir = base / "state"
            profile_input_dir = base / "profile_inputs"
            with input_file.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "keyword",
                        "title",
                        "website",
                        "domain",
                        "country",
                        "industry",
                        "matched_keywords",
                        "matched_countries",
                        "matched_industries",
                        "matched_industry_terms",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "keyword": "heat pump installer Germany",
                        "title": "Acme HVAC",
                        "website": "https://acme.example",
                        "domain": "acme.example",
                        "country": "Germany",
                        "industry": "heat_pump",
                        "matched_keywords": "heat pump installer Germany",
                        "matched_countries": "Germany",
                        "matched_industries": "heat_pump",
                        "matched_industry_terms": "heat pump installer",
                    }
                )
            fetcher = FakeFetcher()

            run_crawl(
                input_file=input_file,
                output_file=output_file,
                state_dir=state_dir,
                workers=1,
                max_depth=0,
                max_pages_per_site=1,
                fetcher=fetcher,
                profile_input_dir=profile_input_dir,
                profile_page_char_limit=500,
            )

            package_path = profile_input_dir / "acme.example.json"
            package = json.loads(package_path.read_text(encoding="utf-8"))

        self.assertEqual(package["schema_version"], "1.0")
        self.assertEqual(package["company"]["domain"], "acme.example")
        self.assertEqual(package["company"]["source_keyword"], "heat pump installer Germany")
        self.assertEqual(package["company"]["matched_industries"], "heat_pump")
        self.assertIn("sales@example.com", package["contacts"]["emails"])
        self.assertEqual(package["pages"][0]["category"], "home")
        self.assertIn("Email: sales@example.com", package["pages"][0]["text"])
        self.assertEqual(package["crawl_metadata"]["status"], "success")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m unittest tests/test_run_crawl.py
```

Expected: FAIL because `--profile-input-dir`, `--profile-page-char-limit`, and `profile_input_dir` keyword argument do not exist yet.

- [ ] **Step 3: Import package writer in `run_crawl.py`**

Add this import near the existing pipeline imports:

```python
from profile_analysis.input_package import build_profile_input_package, write_profile_input_package
```

- [ ] **Step 4: Add optional export parameters to `crawl_company`**

Change the function signature:

```python
def crawl_company(
    company: CompanyInput,
    fetcher: HtmlFetcher,
    max_depth: int,
    max_pages_per_site: int,
    profile_input_dir: str | Path | None = None,
    profile_page_char_limit: int = 8000,
) -> dict[str, str]:
```

After `profile = extract_company_profile(...)` and before the returned row, add:

```python
    if profile_input_dir is not None:
        package = build_profile_input_package(
            company=company,
            profile=profile,
            records=records,
            status="success",
            errors=[],
            max_pages=max_pages_per_site,
            page_char_limit=profile_page_char_limit,
        )
        write_profile_input_package(package, profile_input_dir)
```

- [ ] **Step 5: Add optional export parameters to `run_crawl`**

Change the `run_crawl` signature:

```python
def run_crawl(
    input_file: str | Path = INPUT_FILE,
    output_file: str | Path = OUTPUT_FILE,
    state_dir: str | Path = STATE_DIR,
    workers: int | None = None,
    max_depth: int = 2,
    max_pages_per_site: int = 12,
    retry_failed_only: bool = False,
    fetcher_config: FetcherConfig | None = None,
    browser_fetch_config: BrowserFetchConfig | None = None,
    backend: str = "requests",
    fetcher: HtmlFetcher | None = None,
    profile_input_dir: str | Path | None = None,
    profile_page_char_limit: int = 8000,
) -> list[dict[str, str]]:
```

After the existing `max_pages_per_site` validation, add:

```python
    if profile_page_char_limit < 1:
        raise ValueError("profile_page_char_limit must be >= 1")
```

In the single-worker branch, change the `crawl_company` call to:

```python
                    row = crawl_company(
                        company,
                        active_fetcher,
                        max_depth,
                        max_pages_per_site,
                        profile_input_dir=profile_input_dir,
                        profile_page_char_limit=profile_page_char_limit,
                    )
```

In the multi-worker branch, change the executor submission to:

```python
                    executor.submit(
                        crawl_company,
                        company,
                        active_fetcher,
                        max_depth,
                        max_pages_per_site,
                        profile_input_dir,
                        profile_page_char_limit,
                    ): company
```

- [ ] **Step 6: Add CLI flags to `build_parser` and pass them through `main`**

Add parser arguments after `--output`:

```python
    parser.add_argument(
        "--profile-input-dir",
        default="",
        help="Optional directory for per-company JSON input packages for the profile-analysis Codex",
    )
    parser.add_argument(
        "--profile-page-char-limit",
        type=int,
        default=8000,
        help="Maximum visible text characters per crawled page in profile-analysis input packages",
    )
```

In `main`, pass these arguments to `run_crawl`:

```python
        profile_input_dir=args.profile_input_dir or None,
        profile_page_char_limit=args.profile_page_char_limit,
```

- [ ] **Step 7: Run targeted tests**

Run:

```bash
python -m unittest tests/test_profile_input_package.py tests/test_run_crawl.py
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add run_crawl.py tests/test_run_crawl.py
git commit -m "feat: export profile input packages from crawl"
```

## Task 3: Add Reusable Prompt For The Separate Analysis Codex

**Files:**
- Create: `docs/profile-analysis-agent-prompt.md`

- [ ] **Step 1: Create prompt document**

Create `docs/profile-analysis-agent-prompt.md`:

````markdown
# Profile Analysis Agent Prompt

Use this prompt in the separate Codex session that analyzes company profiles for a heat pump manufacturer.

## Role

You are a B2B overseas customer profile analysis agent for a heat pump manufacturer.

## Business Context

The company manufactures heat pumps. The goal is to identify and segment overseas B2B leads, including distributors, dealers, installers, HVAC contractors, MEP contractors, local brands, OEM/ODM candidates, and possible manufacturing partners.

## Input

You will receive one JSON company website data package with this structure:

```json
{
  "schema_version": "1.0",
  "company": {
    "domain": "example.com",
    "website": "https://example.com",
    "company_name": "Example GmbH",
    "country": "Germany",
    "industry": "hvac",
    "source_keyword": "HVAC contractor Germany",
    "matched_keywords": "HVAC contractor Germany; heat pump installer Germany",
    "matched_countries": "Germany",
    "matched_industries": "hvac; heat_pump",
    "matched_industry_terms": "HVAC contractor; heat pump installer"
  },
  "contacts": {
    "emails": ["info@example.com"],
    "phones": ["+49 ..."],
    "social_links": {"linkedin": "https://linkedin.com/company/example"},
    "people": [{"name": "Max Muller", "title": "Sales Manager", "email": "max@example.com"}]
  },
  "pages": [
    {
      "url": "https://example.com/services",
      "category": "service",
      "title": "Services",
      "text": "Visible page text..."
    }
  ],
  "crawl_metadata": {
    "crawled_pages": 8,
    "status": "success",
    "errors": [],
    "crawl_time": "2026-06-18T10:00:00+08:00"
  }
}
```

## Task

Read the company package and output one valid JSON object that:

- Summarizes the company factually.
- Builds a customer profile from website evidence.
- Assigns one primary marketing segment.
- Assigns zero or more secondary marketing segments.
- Scores the company with the required scoring dimensions.
- Cites evidence for important claims.
- Suggests a practical message angle for heat pump B2B outreach.
- Suggests the next sales or marketing action.

## Allowed Campaign Segments

Use only these exact values:

- `distributor_dealer`
- `installer_contractor`
- `project_supply_candidate`
- `brand_oem_candidate`
- `manufacturer_competitor_or_partner`
- `low_fit_or_unknown`

## Scoring Rules

Use integer scores from 0 to 100.

```text
fit_score =
product_relevance * 0.30
+ business_type_fit * 0.20
+ cooperation_potential * 0.20
+ contactability * 0.10
+ company_scale_signal * 0.10
+ evidence_confidence * 0.10
```

Dimension meanings:

- `product_relevance`: heat pump, HVAC, heating, cooling, renewable heating, or air conditioning relevance.
- `business_type_fit`: fit for heat pump manufacturer B2B outreach.
- `cooperation_potential`: distributor, dealer, wholesale, partner, installer, project, catalog, brand, supplier, OEM, or similar signals.
- `contactability`: actionable email, phone, contact person, LinkedIn, sales email, purchase email, or owner-level contact.
- `company_scale_signal`: service regions, project cases, team pages, branches, brand representation, product catalogs, hiring, or news.
- `evidence_confidence`: clarity and sufficiency of website evidence.

Priority labels:

- `high`: `fit_score >= 80`, and `product_relevance`, `business_type_fit`, and `evidence_confidence` are all at least 70.
- `medium`: `fit_score` is 60-79, or the company is clearly relevant but has missing contact or cooperation evidence.
- `low`: `fit_score` is 40-59, relevance is weak, contactability is low, or cooperation signals are unclear.
- `exclude`: `fit_score < 40`, or the site is clearly irrelevant, a directory, a media site, a job site, a map/social page, inaccessible, or unsupported by evidence.

## Required Output

Return valid JSON only:

```json
{
  "schema_version": "1.0",
  "domain": "example.com",
  "company_name": "Example GmbH",
  "summary": "Short factual company profile.",
  "customer_profile": {
    "business_types": ["installer_contractor"],
    "products_services": ["heat pump installation", "HVAC service"],
    "served_markets": ["residential", "commercial"],
    "service_regions": ["Germany", "Berlin"],
    "brands_mentioned": ["Brand A"],
    "company_scale_signals": ["multiple service locations", "project gallery"],
    "cooperation_signals": ["installation service", "partner brands"],
    "risk_flags": []
  },
  "campaign": {
    "primary_segment": "installer_contractor",
    "secondary_segments": ["project_supply_candidate"],
    "message_angle": "Offer reliable heat pump supply for residential and commercial installation projects.",
    "recommended_next_action": "Contact sales or owner-level email if available."
  },
  "scores": {
    "fit_score": 84,
    "segment_priority": "high",
    "dimensions": {
      "product_relevance": 90,
      "business_type_fit": 85,
      "cooperation_potential": 80,
      "company_scale_signal": 70,
      "contactability": 95,
      "evidence_confidence": 80
    }
  },
  "evidence": [
    {
      "field": "product_relevance",
      "source_url": "https://example.com/services",
      "quote_or_summary": "The services page mentions heat pump installation and maintenance.",
      "confidence": "high"
    }
  ],
  "analysis_notes": "Useful for heat pump supply outreach, but no explicit distributor role found."
}
```

## Constraints

- Do not infer that a company sells or installs heat pumps from the search keyword alone.
- Do not invent emails, phone numbers, brands, regions, company size, products, or business types.
- Lower `evidence_confidence` when evidence is thin, indirect, or only appears on one weak page.
- If the company is a manufacturer, use `manufacturer_competitor_or_partner` and explain whether it appears more like a competitor, OEM/ODM prospect, or possible partner.
- If the company has strong HVAC, heating, cooling, or air conditioning evidence but no explicit heat pump evidence, keep it in scope with lower `product_relevance`.
- For high or medium priority, include at least two meaningful evidence items when available.
- For low or exclude priority, include the reason and the strongest available evidence or lack-of-evidence explanation.
- Keep `summary` factual.
- Keep `message_angle` practical for a heat pump manufacturer outreach campaign.
````

- [ ] **Step 2: Verify prompt contains required segment values**

Run:

```bash
for value in distributor_dealer installer_contractor project_supply_candidate brand_oem_candidate manufacturer_competitor_or_partner low_fit_or_unknown; do rg "$value" docs/profile-analysis-agent-prompt.md >/dev/null || exit 1; done
```

Expected: exit code 0.

- [ ] **Step 3: Commit**

```bash
git add docs/profile-analysis-agent-prompt.md
git commit -m "docs: add profile analysis agent prompt"
```

## Task 4: Document The New Export Workflow

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add README section after "抓取企业公开信息"**

Insert this section after the command that runs `python run_crawl.py`:

````markdown
### 4. 导出画像分析输入包

如果要把抓取结果交给单独的画像分析 Codex，可以在抓取时增加 `--profile-input-dir`：

```bash
python run_crawl.py --profile-input-dir profile_inputs
```

输出：

```text
profile_inputs/<domain>.json
```

每个 JSON 文件包含：

- 公司官网、域名、搜索来源关键词和匹配到的国家/行业信息。
- 抓取到的页面 URL、页面类别、页面标题和可见文本。
- 规则提取出的邮箱、电话、社交链接和联系人。
- 抓取状态、页面数量和抓取时间。

这个 JSON 是给画像分析 Codex 使用的输入包。当前项目只负责生成输入包，不直接判断客户优先级，也不调用 AI。

如需限制每个页面写入的文本长度：

```bash
python run_crawl.py --profile-input-dir profile_inputs --profile-page-char-limit 5000
```
````

- [ ] **Step 2: Verify README references the new flags**

Run:

```bash
rg -n "profile-input-dir|profile-page-char-limit|profile_inputs" README.md
```

Expected: at least three matching lines.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document profile input export workflow"
```

## Task 5: Full Verification And Worklog Update

**Files:**
- Modify: `AI_WORKLOG.md`

- [ ] **Step 1: Run targeted and full tests**

Run:

```bash
python -m unittest tests/test_profile_input_package.py tests/test_run_crawl.py
python -m unittest discover -s tests
```

Expected: all tests PASS.

- [ ] **Step 2: Run a local sample export with fake-safe settings**

Use the existing input CSV and avoid network expansion beyond the crawler's normal behavior by limiting pages:

```bash
python run_crawl.py --input company_websites.csv --output /tmp/profile_export_check_company_info.csv --state-dir /tmp/profile_export_check_state --max-depth 0 --max-pages-per-site 1 --workers 1 --profile-input-dir /tmp/profile_export_check_inputs --profile-page-char-limit 1000
```

Expected:

- Command completes or reports crawl errors per domain without crashing.
- `/tmp/profile_export_check_inputs` exists when at least one domain is crawled successfully.
- Generated JSON files contain `schema_version`, `company`, `contacts`, `pages`, and `crawl_metadata`.

- [ ] **Step 3: Inspect generated sample JSON shape**

Run:

```bash
find /tmp/profile_export_check_inputs -name '*.json' -maxdepth 1 | head -1 | xargs -I{} python -m json.tool {} >/tmp/profile_export_check_sample.json
```

Expected: exit code 0 if at least one JSON file was generated.

- [ ] **Step 4: Append worklog entry**

Append this entry to `AI_WORKLOG.md`:

```markdown
## 2026-06-18 - Profile Input Package Export Implementation

### User Context
- The user approved entering the implementation plan for the lead profile analysis protocol.
- First implementation scope is the handoff layer: generate JSON input packages and a reusable prompt for a separate profile-analysis Codex.

### Work Summary
- Added `profile_analysis/input_package.py` to build per-company JSON input packages from crawled pages and extracted contacts.
- Added optional `run_crawl.py --profile-input-dir` and `--profile-page-char-limit` support.
- Added `docs/profile-analysis-agent-prompt.md` for the separate profile-analysis Codex.
- Updated README usage instructions.

### Files Touched
- `profile_analysis/__init__.py`
- `profile_analysis/input_package.py`
- `tests/test_profile_input_package.py`
- `run_crawl.py`
- `tests/test_run_crawl.py`
- `docs/profile-analysis-agent-prompt.md`
- `README.md`
- `AI_WORKLOG.md`

### Verification
- `python -m unittest tests/test_profile_input_package.py tests/test_run_crawl.py`
- `python -m unittest discover -s tests`
- Sample `run_crawl.py --profile-input-dir ...` export check.

### Next Steps
- Open a separate Codex session with `docs/profile-analysis-agent-prompt.md`.
- Feed it sample `profile_inputs/<domain>.json` files and calibrate profile judgments.
```

- [ ] **Step 5: Commit**

```bash
git add AI_WORKLOG.md
git commit -m "docs: record profile input package implementation"
```

## Final Verification

Run:

```bash
git status --short
python -m unittest discover -s tests
```

Expected:

- `git status --short` shows no uncommitted implementation files.
- Full unittest suite passes.

## Rollback Notes

If the package export causes problems, revert the implementation commits in reverse order. The existing CSV crawl behavior remains isolated because `profile_input_dir` defaults to disabled and the new package writer only runs when that option is provided.
