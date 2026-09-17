"""Facade publique MemorySelector."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from .config import Settings
from .errors import ConfigurationError
from .models import DroppedMemory, MemoryItem, SelectionRequest, SelectionResult
from .providers.custom import CustomProvider
from .providers.gateway import GatewayClient
from .providers.jev import JevClient
from .providers.local import LocalProvider
from .providers.mock import MockProvider
from .security.redaction import redact_item
from .selector import HeuristicSelector


class MemorySelector:
    """Point d'entrée unique : local, mock, custom ou jev+gateway."""

    def __init__(
        self,
        provider: str = "local",
        *,
        api_key: str | None = None,
        jev_base_url: str | None = None,
        gateway_api_key: str | None = None,
        gateway_base_url: str | None = None,
        gateway_model: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        env = settings or Settings.from_env()
        name = provider.strip().lower()
        use_env_defaults = settings is not None
        self.provider_name = name
        self.settings = Settings(
            provider=name,
            jev_api_key=_coalesce(api_key, env.jev_api_key),
            jev_base_url=_coalesce(jev_base_url, env.jev_base_url),
            jev_model=env.jev_model,
            gateway_base_url=_coalesce(gateway_base_url, env.gateway_base_url),
            gateway_api_key=_coalesce(gateway_api_key, env.gateway_api_key),
            gateway_model=_coalesce(gateway_model, env.gateway_model),
            max_candidates=env.max_candidates,
            max_results=env.max_results,
            max_tokens=env.max_tokens,
            min_relevance=env.min_relevance if (name == "jev" or use_env_defaults) else 0.0,
            redact_secrets=env.redact_secrets if use_env_defaults else name in {"jev", "custom"},
            host=env.host,
            port=env.port,
            auth_token=env.auth_token,
            w_jev=env.w_jev,
            w_gateway=env.w_gateway,
            w_similarity=env.w_similarity,
            w_recency=env.w_recency,
            w_importance=env.w_importance,
            request_timeout=env.request_timeout,
        )
        self._validate()

    def _validate(self) -> None:
        if self.provider_name not in {"local", "mock", "custom", "jev"}:
            raise ConfigurationError(f"unknown provider: {self.provider_name}")
        if self.provider_name == "jev":
            missing = [
                name
                for name, value in (
                    ("JEV_API_KEY", self.settings.jev_api_key),
                    ("JEV_BASE_URL", self.settings.jev_base_url),
                    ("GATEWAY_API_KEY", self.settings.gateway_api_key),
                    ("GATEWAY_BASE_URL", self.settings.gateway_base_url),
                    ("GATEWAY_MODEL", self.settings.gateway_model),
                )
                if not value
            ]
            if missing:
                raise ConfigurationError(
                    "provider jev requires " + ", ".join(missing)
                )
        if self.provider_name == "custom" and not self.settings.jev_base_url:
            raise ConfigurationError("JEV_BASE_URL is required for the custom provider")

    def select(
        self,
        query: str,
        memories: Sequence[MemoryItem | Mapping[str, Any]],
        max_memories: int | None = None,
        max_tokens: int | None = None,
        scope: str = "default",
        now: datetime | None = None,
    ) -> SelectionResult:
        items = [MemoryItem.from_mapping(item) for item in memories]
        if self.settings.redact_secrets:
            items = [redact_item(item) for item in items]
        request = SelectionRequest(
            query=query,
            scope=scope,
            budget_tokens=max_tokens or self.settings.max_tokens,
            max_items=max_memories or self.settings.max_results,
            now=now,
        )
        if self.provider_name == "jev":
            return self._select_jev(items, request)
        if self.provider_name == "custom":
            return CustomProvider(
                base_url=self.settings.jev_base_url or "",
                api_key=self.settings.jev_api_key,
                timeout=self.settings.request_timeout,
                selector=self._local_selector(),
            ).select(items, request)
        if self.provider_name == "mock":
            return MockProvider().select(items, request)
        return LocalProvider(self._local_selector()).select(items, request)

    def _local_selector(self) -> HeuristicSelector:
        return HeuristicSelector(min_relevance=self.settings.min_relevance)

    def _hybrid_selector(self) -> HeuristicSelector:
        settings = self.settings
        return HeuristicSelector(
            w_relevance=0.0,
            w_jev=settings.w_jev,
            w_gateway=settings.w_gateway,
            w_similarity=settings.w_similarity,
            w_recency=settings.w_recency,
            w_importance=settings.w_importance,
            min_relevance=settings.min_relevance,
        )

    def _select_jev(self, items: list[MemoryItem], request: SelectionRequest) -> SelectionResult:
        prefilter = HeuristicSelector(min_relevance=self.settings.min_relevance)
        candidates, dropped = prefilter.collect(items, request)
        limited = candidates[: self.settings.max_candidates]
        for _score, _relevance, _recency, item in candidates[self.settings.max_candidates :]:
            dropped.append(DroppedMemory(item.id, "max_candidates"))
        top = [item for _score, _rel, _rec, item in limited]
        if not top:
            return SelectionResult(selected=(), dropped=tuple(dropped), total_tokens=0)

        jev = JevClient(
            api_key=self.settings.jev_api_key or "",
            base_url=self.settings.jev_base_url or "",
            model=self.settings.jev_model,
            timeout=self.settings.request_timeout,
        )
        gateway = GatewayClient(
            api_key=self.settings.gateway_api_key or "",
            base_url=self.settings.gateway_base_url or "",
            model=self.settings.gateway_model or "",
            timeout=self.settings.request_timeout,
        )
        with ThreadPoolExecutor(max_workers=2) as pool:
            jev_future = pool.submit(jev.score, request.query, top)
            gw_future = pool.submit(gateway.score, request.query, top)
            jev_scores = jev_future.result()
            gateway_scores = gw_future.result()

        result = self._hybrid_selector().select(
            top, request, jev_scores=jev_scores, gateway_scores=gateway_scores
        )
        return SelectionResult(
            selected=result.selected,
            dropped=tuple(dropped) + result.dropped,
            total_tokens=result.total_tokens,
        )


def _coalesce(explicit: str | None, fallback: str | None) -> str | None:
    return explicit if explicit is not None else fallback
