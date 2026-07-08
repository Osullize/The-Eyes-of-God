from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen as default_urlopen

from ai.lead_profile_prompt import RESULT_JSON_SCHEMA, SYSTEM_PROMPT


DEFAULT_MODEL_PROVIDER = "deepseek"
DEFAULT_API_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL_NAME = "deepseek-v4-pro"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT_SECONDS = 180.0

UrlOpen = Callable[..., Any]


@dataclass(frozen=True)
class ModelAPIResult:
    content: dict[str, Any]
    raw_response: dict[str, Any]


class ModelAPIError(RuntimeError):
    pass


class ModelAPIClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_API_BASE_URL,
        model: str = DEFAULT_MODEL_NAME,
        temperature: float = DEFAULT_TEMPERATURE,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        urlopen: UrlOpen = default_urlopen,
    ) -> None:
        self.api_key = api_key.strip()
        if not self.api_key:
            raise ValueError("api_key is required")
        self.base_url = (base_url.strip() or DEFAULT_API_BASE_URL).rstrip("/")
        self.model = model.strip() or DEFAULT_MODEL_NAME
        self.temperature = float(temperature)
        self.timeout_seconds = float(timeout_seconds)
        self.urlopen = urlopen

    def analyze_profile(self, profile_payload: dict[str, Any]) -> ModelAPIResult:
        request_payload = {
            "model": self.model,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "schema": RESULT_JSON_SCHEMA,
                            "profile_package": profile_payload,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with self.urlopen(request, timeout=self.timeout_seconds) as response:
                response_text = response.read().decode("utf-8")
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ModelAPIError(f"Model API failed with HTTP {error.code}: {detail[:500]}") from error
        except URLError as error:
            raise ModelAPIError(f"Model API request failed: {error.reason}") from error

        raw_response = self._parse_json(response_text, "Model API returned invalid JSON response")
        content = self._extract_content(raw_response)
        return ModelAPIResult(content=content, raw_response=self._safe_raw_response(raw_response))

    @classmethod
    def _extract_content(cls, raw_response: Any) -> dict[str, Any]:
        try:
            message = raw_response["choices"][0]["message"]
            content = message.get("content") or ""
        except (KeyError, IndexError, TypeError) as error:
            raise ModelAPIError("Model API response does not contain choices[0].message.content") from error
        parsed = cls._parse_json(str(content), "Model API message content is not valid JSON")
        if not isinstance(parsed, dict):
            raise ModelAPIError("Model API message content is not a JSON object")
        return parsed

    @staticmethod
    def _parse_json(value: str, message: str) -> Any:
        try:
            return json.loads(value)
        except json.JSONDecodeError as error:
            raise ModelAPIError(f"{message}: {error}") from error

    @staticmethod
    def _safe_raw_response(raw_response: Any) -> dict[str, Any]:
        if isinstance(raw_response, dict):
            return raw_response
        return {"raw": raw_response}
