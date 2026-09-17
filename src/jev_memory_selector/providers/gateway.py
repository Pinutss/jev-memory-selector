"""Juge LLM via une gateway OpenAI-compatible."""
from __future__ import annotations

import json
import re
from typing import Any

from ..errors import ConfigurationError, ProviderError
from ..models import MemoryItem
from .http import completions_url, post_json
from .scores import parse_score_list

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.I)


class GatewayClient:
    """POST /chat/completions. N'accepte que GATEWAY_API_KEY."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ConfigurationError("GATEWAY_API_KEY is required for the jev provider")
        if not base_url:
            raise ConfigurationError("GATEWAY_BASE_URL is required for the jev provider")
        if not model:
            raise ConfigurationError("GATEWAY_MODEL is required for the jev provider")
        self._api_key = api_key
        self._url = completions_url(base_url)
        self._model = model
        self._timeout = timeout

    def score(self, query: str, items: list[MemoryItem]) -> dict[str, float]:
        catalog = [{"id": item.id, "content": item.text} for item in items]
        prompt = (
            "You judge how relevant memories are. "
            "Reply with JSON only: "
            '{"scores":[{"id":"...","score":0.0,"reason":"..."}]} '
            "score between 0 and 1.\n"
            f"Query: {query}\n"
            f"Memories: {json.dumps(catalog, ensure_ascii=False)}"
        )
        payload = {
            "model": self._model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        response = post_json(self._url, payload, headers, timeout=self._timeout)
        return parse_score_list(_content_from_chat(response))


def _content_from_chat(response: Any) -> Any:
    if not isinstance(response, dict):
        raise ProviderError("invalid gateway response")
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderError("gateway response has no choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise ProviderError("gateway response has no message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ProviderError("empty gateway response")
    cleaned = _FENCE_RE.sub("", content.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ProviderError("invalid gateway judge JSON") from exc
