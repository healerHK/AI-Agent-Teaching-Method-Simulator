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
import time
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
    provider_aliases = {"claude": "anthropic", "google": "gemini"}
    provider = provider_aliases.get(provider, provider)
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
    timeout_seconds = float(
        os.getenv(f"{condition_prefix}_EVALUATOR_TIMEOUT_SECONDS")
        or os.getenv("EVALUATOR_TIMEOUT_SECONDS")
        or "60"
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
        timeout_seconds=timeout_seconds,
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


def evaluator_provider_status(condition: str) -> dict[str, Any]:
    """Return safe provider metadata for UI/testing diagnostics.

    This intentionally reports only booleans/labels, never raw API keys or request URLs
    containing keys.
    """

    config = evaluator_provider_config(condition)
    return {
        "condition": condition,
        "provider": config.provider,
        "model": config.model,
        "model_label": config.model_label,
        "api_key_configured": bool(config.api_key),
        "base_url_configured": bool(config.base_url),
        "temperature": config.temperature,
    }


def _normalize_gemini_model_name(model: str) -> str:
    """Gemini REST URLs expect model name without a leading `models/`."""

    return model.removeprefix("models/").strip()


def _gemini_model_candidates(requested_model: str) -> list[str]:
    """Return requested Gemini model plus compatible Flash fallbacks.

    Some Google projects can list a model but fail actual generation for new users.
    Keep the requested model first, then try conservative Flash aliases if the failure
    is specifically model-availability related.
    """

    configured_fallbacks = [
        value.strip()
        for value in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.6-flash,gemini-flash-latest").split(",")
        if value.strip()
    ]
    candidates: list[str] = []
    for model in [requested_model, *configured_fallbacks]:
        normalized = _normalize_gemini_model_name(model)
        if normalized and normalized not in candidates:
            candidates.append(normalized)
    return candidates


def _is_gemini_model_availability_error(exc: httpx.HTTPStatusError) -> bool:
    """Return True only for errors where trying the next Gemini model is useful."""

    response = exc.response
    status_code = response.status_code if response is not None else None
    if status_code not in {400, 404}:
        return False
    try:
        payload = response.json()
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        status = str(error.get("status", "")).upper()
        message = str(error.get("message", "")).lower()
    except Exception:
        status = ""
        message = ""
    return status in {"NOT_FOUND", "INVALID_ARGUMENT"} and "model" in message


def _is_temperature_unsupported_error(exc: httpx.HTTPStatusError) -> bool:
    """Detect providers/models that require default or omitted temperature."""

    response = exc.response
    if response is None or response.status_code != 400:
        return False
    try:
        payload = response.json()
    except Exception:
        return False
    text = json.dumps(payload, ensure_ascii=False).lower()
    return "temperature" in text and (
        "unsupported" in text
        or "deprecated" in text
        or "only the default" in text
    )


TRANSIENT_HTTP_STATUSES = {429, 500, 502, 503, 504}


def _post_json_with_retries(
    client: httpx.Client,
    url: str,
    *,
    json_payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    attempts: int = 3,
) -> httpx.Response:
    """POST JSON with conservative retries for transient provider failures."""

    last_exc: httpx.HTTPStatusError | None = None
    last_timeout: httpx.TimeoutException | None = None
    for attempt in range(attempts):
        try:
            response = client.post(url, headers=headers, json=json_payload)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as exc:
            last_timeout = exc
            if attempt >= attempts - 1:
                raise
            time.sleep(1.5 * (2**attempt))
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            status = exc.response.status_code if exc.response is not None else None
            if status not in TRANSIENT_HTTP_STATUSES or attempt >= attempts - 1:
                raise
            time.sleep(1.5 * (2**attempt))
    if last_exc is not None:
        raise last_exc
    assert last_timeout is not None
    raise last_timeout


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
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if _is_temperature_unsupported_error(exc):
                    payload.pop("temperature", None)
                    self.config.temperature = 1.0
                    response = client.post(
                        f"{base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self.config.api_key}"},
                        json=payload,
                    )
                    response.raise_for_status()
                else:
                    raise
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _anthropic(self, *, system_prompt: str, user_prompt: str) -> str:
        assert self.config.api_key
        base_url = (self.config.base_url or "https://api.anthropic.com/v1").rstrip("/")
        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": 2000,
            "thinking": {"type": "disabled"},
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
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if _is_temperature_unsupported_error(exc):
                    payload.pop("temperature", None)
                    self.config.temperature = 1.0
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
                else:
                    raise
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
        last_model_error: httpx.HTTPStatusError | None = None
        for model in _gemini_model_candidates(self.config.model):
            with httpx.Client(timeout=self.config.timeout_seconds) as client:
                try:
                    response = _post_json_with_retries(
                        client,
                        f"{base_url}/models/{model}:generateContent?key={self.config.api_key}",
                        json_payload=payload,
                    )
                except httpx.HTTPStatusError as exc:
                    if _is_gemini_model_availability_error(exc):
                        last_model_error = exc
                        continue
                    raise
            self.config.model = model
            data = response.json()
            parts = data["candidates"][0]["content"].get("parts", [])
            return "\n".join(part.get("text", "") for part in parts)
        if last_model_error is not None:
            raise last_model_error
        raise RuntimeError("No Gemini model candidates configured")


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
