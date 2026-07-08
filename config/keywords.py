from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_KEYWORDS_PATH = Path(__file__).with_name("keywords.yaml")


@dataclass(frozen=True)
class KeywordSpec:
    keyword: str
    country: str
    country_term: str
    industry: str
    industry_term: str


def _strip_yaml_value(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def _load_keyword_yaml_subset(path: Path) -> dict[str, Any]:
    """Small fallback parser for this repository's keywords.yaml shape.

    PyYAML is the preferred parser when installed. This keeps local validation
    working in minimal Python environments without accepting arbitrary YAML.
    """
    data: dict[str, Any] = {"countries": {}, "industries": {}}
    current_section = ""
    current_name = ""
    current_list = ""

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indent == 0 and line.endswith(":"):
            current_section = line[:-1]
            data.setdefault(current_section, {})
            current_name = ""
            current_list = ""
            continue

        if indent == 2 and line.endswith(":"):
            current_name = line[:-1]
            data[current_section].setdefault(current_name, {})
            current_list = ""
            continue

        if indent == 4 and line.endswith(":"):
            current_list = line[:-1]
            data[current_section][current_name].setdefault(current_list, [])
            continue

        if indent >= 6 and line.startswith("- "):
            data[current_section][current_name][current_list].append(_strip_yaml_value(line[2:]))
            continue

        raise ValueError(f"Unsupported keywords.yaml line: {raw_line}")

    return data


def load_keyword_config(path: str | Path = DEFAULT_KEYWORDS_PATH) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Keyword config not found: {config_path}")

    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        return _load_keyword_yaml_subset(config_path)

    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"Keyword config must be a YAML mapping: {config_path}")
    return loaded


def _terms_from_node(node: Any, node_name: str) -> list[str]:
    if isinstance(node, list):
        terms = [str(item).strip() for item in node if str(item).strip()]
    elif isinstance(node, dict):
        terms = []
        for key in ("terms", "synonyms"):
            values = node.get(key, [])
            if isinstance(values, str):
                values = [values]
            terms.extend(str(item).strip() for item in values if str(item).strip())
    elif isinstance(node, str):
        terms = [node.strip()]
    else:
        raise ValueError(f"Invalid keyword config node for {node_name!r}: {node!r}")

    if not terms:
        raise ValueError(f"Keyword config node has no terms: {node_name}")
    return terms


def build_keywords_from_config(path: str | Path = DEFAULT_KEYWORDS_PATH) -> list[KeywordSpec]:
    config = load_keyword_config(path)
    countries = config.get("countries", {})
    industries = config.get("industries", {})

    if not isinstance(countries, dict) or not countries:
        raise ValueError("Keyword config must define a non-empty countries mapping")
    if not isinstance(industries, dict) or not industries:
        raise ValueError("Keyword config must define a non-empty industries mapping")

    keyword_specs: list[KeywordSpec] = []
    for country, country_node in countries.items():
        country_terms = _terms_from_node(country_node, str(country))
        for country_term in country_terms:
            for industry, industry_node in industries.items():
                industry_terms = _terms_from_node(industry_node, str(industry))
                for industry_term in industry_terms:
                    keyword_specs.append(
                        KeywordSpec(
                            keyword=f"{industry_term} {country_term}",
                            country=str(country),
                            country_term=country_term,
                            industry=str(industry),
                            industry_term=industry_term,
                        )
                    )

    return keyword_specs
