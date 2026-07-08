from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config.keywords import DEFAULT_KEYWORDS_PATH, _strip_yaml_value


DEFAULT_SEARCH_CONFIG_PATH = Path(__file__).with_name("search.yaml")


@dataclass(frozen=True)
class SearchRuntimeConfig:
    keyword_config: str = str(DEFAULT_KEYWORDS_PATH)
    output: str = "company_websites.csv"
    state_dir: str = ".search_state"
    backend: str = "browser"
    engines: tuple[str, ...] = ("duckduckgo",)
    max_pages: int = 2
    limit_keywords: int | None = None
    retry_failed: bool = False
    keyword_delay: float = 30.0
    engine_request_delay: float = 10.0
    max_retries: int = 3
    backoff_base: float = 20.0
    backoff_max: float = 180.0
    proxy: str = ""
    use_system_proxy: bool = True
    headless: bool = True
    browser_max_pages: int = 1


def _parse_scalar(value: str) -> Any:
    value = _strip_yaml_value(value)
    lower = value.lower()
    if lower in {"true", "yes", "on"}:
        return True
    if lower in {"false", "no", "off"}:
        return False
    if lower in {"null", "none", "~"}:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _load_search_yaml_subset(path: Path) -> dict[str, Any]:
    """Small fallback parser for this repository's flat search.yaml shape."""
    data: dict[str, Any] = {}
    current_list = ""

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indent == 0:
            key, separator, raw_value = line.partition(":")
            if not separator:
                raise ValueError(f"Unsupported search.yaml line: {raw_line}")
            key = key.strip()
            raw_value = raw_value.strip()
            if raw_value:
                data[key] = _parse_scalar(raw_value)
                current_list = ""
            else:
                data[key] = []
                current_list = key
            continue

        if indent >= 2 and line.startswith("- ") and current_list:
            value = _parse_scalar(line[2:].strip())
            data[current_list].append(value)
            continue

        raise ValueError(f"Unsupported search.yaml line: {raw_line}")

    return data


def _as_bool(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        parsed = _parse_scalar(value)
        if isinstance(parsed, bool):
            return parsed
    raise ValueError(f"Search config field {field!r} must be a boolean")


def _as_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"Search config field {field!r} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Search config field {field!r} must be an integer") from error


def _as_float(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"Search config field {field!r} must be a number")
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Search config field {field!r} must be a number") from error


def _as_engines(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        engines = tuple(item.strip() for item in value.split(",") if item.strip())
    elif isinstance(value, (list, tuple)):
        engines = tuple(str(item).strip() for item in value if str(item).strip())
    else:
        raise ValueError("Search config field 'engines' must be a list or comma-separated string")

    if not engines:
        raise ValueError("Search config field 'engines' must not be empty")
    return engines


def _build_config(data: dict[str, Any]) -> SearchRuntimeConfig:
    defaults = SearchRuntimeConfig()

    config = SearchRuntimeConfig(
        keyword_config=str(data.get("keyword_config", defaults.keyword_config)),
        output=str(data.get("output", defaults.output)),
        state_dir=str(data.get("state_dir", defaults.state_dir)),
        backend=str(data.get("backend", defaults.backend)),
        engines=_as_engines(data.get("engines", defaults.engines)),
        max_pages=_as_int(data.get("max_pages", defaults.max_pages), "max_pages"),
        limit_keywords=(
            None
            if data.get("limit_keywords", defaults.limit_keywords) is None
            else _as_int(data.get("limit_keywords"), "limit_keywords")
        ),
        retry_failed=_as_bool(data.get("retry_failed", defaults.retry_failed), "retry_failed"),
        keyword_delay=_as_float(data.get("keyword_delay", defaults.keyword_delay), "keyword_delay"),
        engine_request_delay=_as_float(
            data.get("engine_request_delay", defaults.engine_request_delay),
            "engine_request_delay",
        ),
        max_retries=_as_int(data.get("max_retries", defaults.max_retries), "max_retries"),
        backoff_base=_as_float(data.get("backoff_base", defaults.backoff_base), "backoff_base"),
        backoff_max=_as_float(data.get("backoff_max", defaults.backoff_max), "backoff_max"),
        proxy=str(data.get("proxy", defaults.proxy) or ""),
        use_system_proxy=_as_bool(data.get("use_system_proxy", defaults.use_system_proxy), "use_system_proxy"),
        headless=_as_bool(data.get("headless", defaults.headless), "headless"),
        browser_max_pages=_as_int(data.get("browser_max_pages", defaults.browser_max_pages), "browser_max_pages"),
    )

    if config.backend not in {"requests", "browser"}:
        raise ValueError("Search config field 'backend' must be 'requests' or 'browser'")
    if config.max_pages < 1:
        raise ValueError("Search config field 'max_pages' must be >= 1")
    if config.max_retries < 1:
        raise ValueError("Search config field 'max_retries' must be >= 1")
    if config.browser_max_pages < 1:
        raise ValueError("Search config field 'browser_max_pages' must be >= 1")

    return config


def load_search_config(path: str | Path = DEFAULT_SEARCH_CONFIG_PATH) -> SearchRuntimeConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Search config not found: {config_path}")

    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        loaded = _load_search_yaml_subset(config_path)
    else:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    if not isinstance(loaded, dict):
        raise ValueError(f"Search config must be a YAML mapping: {config_path}")
    return _build_config(loaded)
