from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any

from app.core.config import get_settings
from app.core.security import redact_pii


class LLMUnavailable(RuntimeError):
    pass


@dataclass
class LLMResult:
    content: str
    model: str
    provider: str
    latency_ms: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    fallback_used: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


def _strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def live_enabled(self) -> bool:
        return self.settings.llm_mode == "live"

    def model_for_purpose(self, purpose: str) -> str:
        if purpose in {"classification", "triage"}:
            return self.settings.groq_model
        if purpose in {"verification", "report"}:
            return self.settings.gemini_pro_model
        return self.settings.gemini_flash_model

    def fallback_models(self, primary: str) -> list[str]:
        models = [
            self.settings.gemini_flash_model,
            self.settings.groq_model,
            self.settings.ollama_model,
        ]
        return [model for model in dict.fromkeys(models) if model != primary]

    def api_key_for(self, model: str) -> str | None:
        if model.startswith("gemini/"):
            return self.settings.gemini_api_key or None
        if model.startswith("groq/"):
            return self.settings.groq_api_key or None
        return None

    async def complete(
        self,
        *,
        system: str,
        user: str,
        purpose: str = "extraction",
        json_mode: bool = True,
    ) -> LLMResult:
        if not self.live_enabled:
            raise LLMUnavailable("LLM_MODE=mock; deterministic agent path in use")
        safe_user, _redactions = redact_pii(user)
        primary = self.model_for_purpose(purpose)
        candidates = [primary, *self.fallback_models(primary)]
        errors: list[str] = []
        for index, model in enumerate(candidates):
            try:
                from litellm import acompletion

                started = time.perf_counter()
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": safe_user},
                    ],
                    "timeout": self.settings.llm_timeout_seconds,
                    "temperature": 0.1,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                api_key = self.api_key_for(model)
                if api_key:
                    kwargs["api_key"] = api_key
                response = await acompletion(**kwargs)
                latency_ms = int((time.perf_counter() - started) * 1000)
                content = response.choices[0].message.content or ""  # pyright: ignore[reportAttributeAccessIssue]
                usage = getattr(response, "usage", None)
                return LLMResult(
                    content=content,
                    model=model,
                    provider=model.split("/")[0],
                    latency_ms=latency_ms,
                    prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                    completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                    fallback_used=index > 0,
                )
            except Exception as exc:
                errors.append(f"{model}: {type(exc).__name__}: {exc}")
        raise LLMUnavailable("; ".join(errors[-3:]))

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        purpose: str = "extraction",
    ) -> tuple[dict[str, Any], LLMResult]:
        result = await self.complete(system=system, user=user, purpose=purpose, json_mode=True)
        try:
            parsed = json.loads(_strip_json_fences(result.content))
        except json.JSONDecodeError as exc:
            raise LLMUnavailable(f"Model returned invalid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise LLMUnavailable("Model returned a non-object JSON value")
        return parsed, result


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
