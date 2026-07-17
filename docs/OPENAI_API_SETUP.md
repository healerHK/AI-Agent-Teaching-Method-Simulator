# LLM Provider API Setup

PixelClass TIL Phase 3/4 evaluator pipeline is provider-agnostic. You can test OpenAI, Claude, Gemini, or any OpenAI-compatible provider by changing local config only.

Do **not** commit real API keys.

## Local `.env`

Create:

```text
D:/Code/til-classroom-sim/.env
```

## Fallback mode

Use this when you want tests and demos without provider calls:

```text
EVALUATOR_PROVIDER=fallback
EVALUATOR_MODEL=deterministic-fallback
```

## OpenAI

```text
EVALUATOR_PROVIDER=openai
EVALUATOR_MODEL=gpt-4o-mini
EVALUATOR_API_KEY=your_openai_key
EVALUATOR_TEMPERATURE=0.2
```

## Claude / Anthropic

```text
EVALUATOR_PROVIDER=anthropic
EVALUATOR_MODEL=claude-3-5-sonnet-latest
EVALUATOR_API_KEY=your_anthropic_key
EVALUATOR_TEMPERATURE=0.2
```

## Gemini

```text
EVALUATOR_PROVIDER=gemini
EVALUATOR_MODEL=gemini-2.5-flash
EVALUATOR_API_KEY=your_gemini_key
EVALUATOR_TEMPERATURE=0.2
```

## OpenAI-compatible provider

Use this for OpenRouter, local gateways, or other providers exposing `/chat/completions`:

```text
EVALUATOR_PROVIDER=openai_compatible
EVALUATOR_BASE_URL=https://your-provider.example/v1
EVALUATOR_MODEL=provider/model-name
EVALUATOR_API_KEY=your_provider_key
EVALUATOR_TEMPERATURE=0.2
```

## Per-condition override

You can compare providers by evaluator condition:

```text
BASELINE_EVALUATOR_PROVIDER=openai
BASELINE_EVALUATOR_MODEL=gpt-4o-mini
BASELINE_EVALUATOR_API_KEY=your_openai_key

TIL_EVALUATOR_PROVIDER=anthropic
TIL_EVALUATOR_MODEL=claude-3-5-sonnet-latest
TIL_EVALUATOR_API_KEY=your_anthropic_key
```

## Verification after config change

```bash
cd D:/Code/til-classroom-sim/backend
uv run pytest -q
uv run python -m scripts.run_benchmark --conditions baseline,til --repetitions 1 --transcript-id python_loops_weak_001
```

Frontend smoke test:

```bash
cd D:/Code/til-classroom-sim/frontend
export PATH='/c/Program Files/nodejs':"$PATH"
npm run dev -- --host 127.0.0.1 --port 5173
```
