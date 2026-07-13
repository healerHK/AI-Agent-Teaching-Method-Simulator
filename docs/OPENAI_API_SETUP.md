# OpenAI API Setup

## Current note

The OpenAI API/key/config is expected to be updated tonight. Until then, PixelClass TIL should remain runnable through deterministic fallback mode.

## Local `.env`

Create `D:/Code/til-classroom-sim/.env` locally. Do not commit it.

```text
OPENAI_API_KEY=<new key>
OPENAI_SIMULATION_MODEL=gpt-4o-mini
OPENAI_BASELINE_EVALUATOR_MODEL=gpt-4o-mini
OPENAI_TIL_EVALUATOR_MODEL=gpt-4o
OPENAI_TEMPERATURE_STUDENT=0.7
OPENAI_TEMPERATURE_EVALUATOR=0.2
MAX_TURNS_PER_SESSION=12
EXPORT_ROOT=D:/Mythesis(Honours)/MVP_Outputs
```

## Verification after update

```bash
cd D:/Code/til-classroom-sim/backend
uv run pytest -q
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then run frontend:

```bash
cd D:/Code/til-classroom-sim/frontend
export PATH='/c/Program Files/nodejs':"$PATH"
npm run dev -- --host 127.0.0.1 --port 5173
```

The app should still work without exposing the API key to the frontend.
