# Lead Profile Analysis Protocol Design

## Status

Approved for design by the user on 2026-06-18.

## Background

The project currently searches for company websites, crawls public website pages, extracts basic contact information, and writes CSV outputs. The next product direction is to turn crawled company website information into B2B customer profiles for a heat pump manufacturer.

The user wants to open a separate Codex session and mainly train that Codex to analyze company profiles. Therefore, this project should define a stable handoff protocol: current crawler output becomes structured input for the profile-analysis Codex, and that Codex returns machine-readable profile and marketing segmentation results.

## Goals

- Define the company data package that the current crawler should provide to the profile-analysis Codex.
- Define the output JSON schema that the profile-analysis Codex must return.
- Define fixed marketing campaign segments for first-version analysis.
- Define a multi-dimensional scoring system with segment-level priority.
- Define the prompt structure and evidence requirements for the profile-analysis Codex.
- Keep the crawler and analysis responsibilities separate.

## Non-Goals

- Do not implement code in this design phase.
- Do not let the profile-analysis Codex search the web, click pages, control a browser, or send emails.
- Do not build a CRM, email sender, or marketing automation system in this phase.
- Do not train or fine-tune a model in this phase.

## System Boundary

The current project is responsible for collecting and packaging evidence:

- Company website URL and domain.
- Search source keyword and matched search metadata.
- Country and industry metadata from the search stage.
- Crawled page URLs, page categories, and visible page text.
- Extracted contacts, phones, social links, and contact people.
- Crawl status and basic metadata.

The separate profile-analysis Codex is responsible for analysis:

- Read one company data package.
- Build a customer profile from website evidence.
- Assign a marketing campaign segment.
- Score the company with multi-dimensional criteria.
- Explain the decision with evidence.
- Suggest the marketing message angle and next action.

## Input Data Package

Each company should be passed to the profile-analysis Codex as one JSON object.

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
    "social_links": {
      "linkedin": "https://linkedin.com/company/example"
    },
    "people": [
      {
        "name": "Max Muller",
        "title": "Sales Manager",
        "email": "max@example.com"
      }
    ]
  },
  "pages": [
    {
      "url": "https://example.com/services",
      "category": "service",
      "title": "Services",
      "text": "Full visible page text..."
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

Input rules:

- `pages[].text` should contain visible text, not raw HTML.
- `pages[].category` should reuse the crawler categories where possible: `home`, `contact`, `about`, `team`, `product`, `service`, `news`, or `other`.
- Search-stage metadata must be preserved because it explains why the company was found.
- Contacts extracted by rules should be included, but the profile-analysis Codex must not invent missing contacts.
- First-version packaging may limit page count and text length per company to control cost, but truncation should preserve high-value pages first: home, product, service, about, contact, team, case/news.

## Output JSON Schema

The profile-analysis Codex must return one JSON object per company.

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

Output rules:

- Return valid JSON only. Do not include Markdown or extra prose around the JSON.
- `campaign.primary_segment` must be one of the allowed campaign segments.
- `campaign.secondary_segments` may be empty but must only contain allowed campaign segments.
- `scores.fit_score` and all dimension scores must be integers from 0 to 100.
- `scores.segment_priority` must be `high`, `medium`, `low`, or `exclude`.
- Important claims must be backed by `evidence`.
- Do not fabricate email addresses, brands, regions, company size, products, or business types.

## Campaign Segments

First-version analysis must use these fixed campaign segments:

- `distributor_dealer`
- `installer_contractor`
- `project_supply_candidate`
- `brand_oem_candidate`
- `manufacturer_competitor_or_partner`
- `low_fit_or_unknown`

Segment meanings:

- `distributor_dealer`: distributors, dealers, wholesalers, resellers, suppliers, catalog businesses, and brand-channel companies.
- `installer_contractor`: installers, HVAC contractors, maintenance providers, repair companies, and service contractors.
- `project_supply_candidate`: commercial project companies, construction firms, MEP contractors, engineering firms, building service providers, and companies with case-study or project signals.
- `brand_oem_candidate`: local brands, equipment companies, system integrators, or companies with product lines that may fit OEM/ODM cooperation.
- `manufacturer_competitor_or_partner`: companies that manufacture heat pumps, HVAC equipment, heating equipment, or adjacent products. These should not be automatically excluded because they may be competitors, OEM candidates, or cooperation partners.
- `low_fit_or_unknown`: unrelated companies, weak evidence, directory/media/job/map/social pages, inaccessible sites, or companies that cannot be classified confidently.

## Scoring Model

The first-version score is multi-dimensional and segment-aware.

```text
fit_score =
product_relevance * 0.30
+ business_type_fit * 0.20
+ cooperation_potential * 0.20
+ contactability * 0.10
+ company_scale_signal * 0.10
+ evidence_confidence * 0.10
```

Dimension definitions:

- `product_relevance`: how clearly the website relates to heat pumps, HVAC, heating, cooling, renewable heating, or air conditioning.
- `business_type_fit`: how well the company type fits a heat pump manufacturer B2B outreach motion.
- `cooperation_potential`: whether the site shows dealer, distributor, wholesale, partner, installer, project, catalog, brand, supplier, OEM, or similar cooperation signals.
- `contactability`: whether actionable contact paths exist, including email, phone, named contacts, LinkedIn, sales email, purchase email, or owner-level contact.
- `company_scale_signal`: whether the site shows scale through multiple regions, project cases, team pages, branches, brand representation, product catalogs, hiring, or news.
- `evidence_confidence`: how clear, direct, and sufficient the website evidence is across pages.

Segment priority rules:

- `high`: `fit_score >= 80`, and `product_relevance`, `business_type_fit`, and `evidence_confidence` are all at least 70.
- `medium`: `fit_score` is 60-79, or the company is clearly relevant but has missing contact or cooperation evidence.
- `low`: `fit_score` is 40-59, relevance is weak, contactability is low, or cooperation signals are unclear.
- `exclude`: `fit_score < 40`, or the site is clearly irrelevant, a directory, a media site, a job site, a map/social page, inaccessible, or unsupported by evidence.

Risk rules:

- A manufacturer must not be automatically excluded. Put it into `manufacturer_competitor_or_partner` and explain whether it appears more like a competitor, OEM/ODM prospect, or possible partner.
- A company with no explicit heat pump mention but strong HVAC, heating, cooling, or air conditioning evidence can remain in scope with a lower `product_relevance` score.
- A match from the original search keyword is not enough evidence. The profile-analysis Codex must inspect website text.

## Prompt Structure For The Profile-Analysis Codex

The reusable prompt should contain these sections:

1. `Role`: You are a B2B overseas customer profile analysis agent for a heat pump manufacturer.
2. `Business Context`: The company manufactures heat pumps and wants overseas B2B leads such as distributors, dealers, installers, HVAC contractors, MEP contractors, local brands, OEM/ODM candidates, and possible manufacturing partners.
3. `Input`: You will receive one company website data package with website metadata, search source metadata, page text, page categories, contacts, and crawl metadata.
4. `Task`: Read the package, build a factual customer profile, assign campaign segments, score the company, cite evidence, and suggest the marketing message angle and next action.
5. `Allowed Campaign Segments`: Use only the fixed segment values defined in this document.
6. `Scoring Rules`: Apply the multi-dimensional score and priority rules defined in this document.
7. `Output Contract`: Return valid JSON only, matching the output schema.

Prompt constraints:

- Do not infer that the company sells or installs heat pumps from the search keyword alone.
- Lower `evidence_confidence` when evidence is thin, indirect, or only appears on one weak page.
- For high or medium priority, include at least two meaningful evidence items when available.
- For low or exclude priority, include the reason and the strongest available evidence or lack-of-evidence explanation.
- Do not invent missing information.
- Keep `summary` factual and concise.
- Keep `message_angle` practical for a heat pump manufacturer outreach campaign.

## CSV Summary Fields

The complete JSON should be preserved for automation. A CSV summary can be derived for review and filtering:

```text
domain,
company_name,
primary_segment,
secondary_segments,
fit_score,
segment_priority,
product_relevance,
business_type_fit,
cooperation_potential,
company_scale_signal,
contactability,
evidence_confidence,
message_angle,
recommended_next_action,
summary
```

## Validation

Before using the profile-analysis Codex at scale:

- Run it on a small batch of real crawled companies.
- Manually review high, medium, low, and exclude examples.
- Check whether evidence items support the assigned segment and score.
- Adjust prompt wording and scoring examples based on review results.
- Keep examples of corrected outputs for future calibration.

## Future Implementation Notes

Future implementation can add:

- A data-packaging command that converts crawled pages into per-company JSON input packages.
- A `company_profiles.csv` summary output.
- A `profiles/<domain>.json` directory for complete profile-analysis results.
- Optional later integration where `run_crawl.py` triggers analysis after each successful crawl.

For the first implementation, prefer keeping profile analysis separate from crawling until the profile-analysis prompt and scoring standard are stable.
