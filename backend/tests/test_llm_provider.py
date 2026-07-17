from app.llm_provider import evaluator_provider_config


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
