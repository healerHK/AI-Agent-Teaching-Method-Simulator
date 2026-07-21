from app.llm_provider import _gemini_model_candidates, evaluator_provider_config, evaluator_provider_status


def test_evaluator_provider_defaults_to_fallback(monkeypatch):
    for key in [
        "EVALUATOR_PROVIDER",
        "LLM_PROVIDER",
        "EVALUATOR_API_KEY",
        "LLM_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
    ]:
        monkeypatch.delenv(key, raising=False)

    config = evaluator_provider_config("til")

    assert config.provider == "fallback"
    assert config.model == "deterministic-fallback"


def test_evaluator_provider_can_select_anthropic(monkeypatch):
    monkeypatch.setenv("EVALUATOR_PROVIDER", "anthropic")
    monkeypatch.setenv("EVALUATOR_API_KEY", "fake-key")
    monkeypatch.setenv("EVALUATOR_MODEL", "claude-test")

    config = evaluator_provider_config("baseline")

    assert config.provider == "anthropic"
    assert config.model == "claude-test"
    assert config.api_key == "fake-key"


def test_gemini_model_candidates_normalize_models_prefix(monkeypatch):
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", "models/gemini-flash-latest,gemini-1.5-flash")

    candidates = _gemini_model_candidates("models/gemini-2.5-flash")

    assert candidates == ["gemini-2.5-flash", "gemini-flash-latest", "gemini-1.5-flash"]


def test_evaluator_provider_status_redacts_key(monkeypatch):
    monkeypatch.setenv("EVALUATOR_PROVIDER", "gemini")
    monkeypatch.setenv("EVALUATOR_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("EVALUATOR_API_KEY", "fake-secret-key")

    status = evaluator_provider_status("til")

    assert status["provider"] == "gemini"
    assert status["model"] == "gemini-2.5-flash"
    assert status["api_key_configured"] is True
    assert "fake-secret-key" not in str(status)
