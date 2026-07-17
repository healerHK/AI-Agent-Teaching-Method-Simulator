"""Provider-agnostic LLM client for evaluator experiments.

The thesis needs to compare evaluator behavior across providers. This module keeps
provider selection in configuration rather than hard-coding OpenAI.

Supported provider modes:

- fallback: no network call; evaluator runner uses deterministic fallback output.
- openai: OpenAI Chat Completions API.
- openai_compatible: any OpenAI-compatible endpoint/base URL.
- anthropic: Anthropic Claude Messages API.
- gemini: Google Gemini generateContent API.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from app.config import SUPPORTED_LLM_PROVIDERS

ProviderName = Literal["fallback", "openai", "anthropic", "gemini", "openai_compatible"]


@dataclass
class LLMProviderConfig:
    provider: ProviderName
    model: str
    api_key: str | None
    base_url: str | None
    temperature: float
    timeout_seconds: float = 60.0

    @property
    def model_label(self) -> str:
        return f"{self.provider}:{self.model}"


def evaluator_provider_config(condition: str) -> LLMProviderConfig:
    """Build provider config for baseline/til evaluator condition.

    Precedence is condition-specific -> generic evaluator -> provider-specific legacy
    envs -> fallback defaults. This lets the user switch OpenAI/Claude/Gemini from
    env/config without code changes.
    """

    condition_prefix = condition.upper()
    provider = (
        os.getenv(f"{condition_prefix}_EVALUATOR_PROVIDER")
        or os.getenv("EVALUATOR_PROVIDER")
        or os.getenv("LLM_PROVIDER")
        or "fallback"
    ).strip().lower()
    if provider not in SUPPORTED_LLM_PROVIDERS:
        provider = "fallback"

    model = _model_for_provider(condition_prefix, provider)
    api_key = _api_key_for_provider(condition_prefix, provider)
    base_url = (
        os.getenv(f"{condition_prefix}_EVALUATOR_BASE_URL")
        or os.getenv("EVALUATOR_BASE_URL")
        or os.getenv("LLM_BASE_URL")
        or _default_base_url(provider)
    )
    temperature = float(
        os.getenv(f"{condition_prefix}_EVALUATOR_TEMPERATURE")
        or os.getenv("EVALUATOR_TEMPERATURE")
        or os.getenv("OPENAI_TEMPERATURE_EVALUATOR")
        or "0.2"
    )
    if provider == "fallback":
        model = "deterministic-fallback"
        api_key = None
        base_url = None
    elif not api_key:
        provider = "fallback"
        model = "deterministic-fallback"
        base_url = None

    return LLMProviderConfig(
        provider=provider,  # type: ignore[arg-type]
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
    )


def _model_for_provider(condition_prefix: str, provider: str) -> str:
    condition_model = os.getenv(f"{condition_prefix}_EVALUATOR_MODEL")
    generic_model = os.getenv("EVALUATOR_MODEL") or os.getenv("LLM_MODEL")
    legacy_openai_model = os.getenv(f"OPENAI_{condition_prefix}_EVALUATOR_MODEL")
    if condition_model:
        return condition_model
    if generic_model:
        return generic_model
    if legacy_openai_model:
        return legacy_openai_model
    defaults = {
        "openai": "gpt-4o-mini",
        "openai_compatible": "gpt-4o-mini",
        "anthropic": "claude-3-5-sonnet-latest",
        "gemini": "gemini-2.5-flash",
        "fallback": "deterministic-fallback",
    }
    return defaults.get(provider, "deterministic-fallback")


def _api_key_for_provider(condition_prefix: str, provider: str) -> str | None:
    key = (
        os.getenv(f"{condition_prefix}_EVALUATOR_API_KEY")
        or os.getenv("EVALUATOR_API_KEY")
        or os.getenv("LLM_API_KEY")
        or os.getenv(f"{provider.upper()}_API_KEY")
    )
    if key:
        return key
    if provider in {"openai", "openai_compatible"}:
        return os.getenv("OPENAI_API_KEY")
    if provider == "anthropic":
        return os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    if provider == "gemini":
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return None


def _default_base_url(provider: str) -> str | None:
    if provider == "openai":
        return "https://api.openai.com/v1"
    if provider == "anthropic":
        return "https://api.anthropic.com/v1"
    if provider == "gemini":
        return "https://generativelanguage.googleapis.com/v1beta"
    return None


class LLMProviderClient:
    def __init__(self, config: LLMProviderConfig) -> None:
        self.config = config

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if self.config.provider == "fallback":
            raise RuntimeError("fallback provider does not make network calls")
        if self.config.provider in {"openai", "openai_compatible"}:
            text = self._openai_compatible(system_prompt=system_prompt, user_prompt=user_prompt)
        elif self.config.provider == "anthropic":
            text = self._anthropic(system_prompt=system_prompt, user_prompt=user_prompt)
        elif self.config.provider == "gemini":
            text = self._gemini(system_prompt=system_prompt, user_prompt=user_prompt)
        else:
            raise RuntimeError(f"Unsupported provider: {self.config.provider}")
        return _extract_json(text)

    def _openai_compatible(self, *, system_prompt: str, user_prompt: str) -> str:
        assert self.config.api_key
        base_url = (self.config.base_url or "https://api.openai.com/v1").rstrip("/")
        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _anthropic(self, *, system_prompt: str, user_prompt: str) -> str:
        assert self.config.api_key
        base_url = (self.config.base_url or "https://api.anthropic.com/v1").rstrip("/")
        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.post(
                f"{base_url}/messages",
                headers={
                    "x-api-key": self.config.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        chunks = data.get("content", [])
        return "\n".join(chunk.get("text", "") for chunk in chunks if chunk.get("type") == "text")

    def _gemini(self, *, system_prompt: str, user_prompt: str) -> str:
        assert self.config.api_key
        base_url = (self.config.base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        prompt = f"{system_prompt}\n\n{user_prompt}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.config.temperature,
                "responseMimeType": "application/json",
            },
        }
        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.post(
                f"{base_url}/models/{self.config.model}:generateContent?key={self.config.api_key}",
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        parts = data["candidates"][0]["content"].get("parts", [])
        return "\n".join(part.get("text", "") for part in parts)


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)
