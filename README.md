# PixelClass TIL

**Teacher-in-the-Loop Agentic AI for Pedagogically Grounded Multi-Agent Classroom Simulation**

PixelClass TIL is a research MVP for comparing generic LLM feedback with a theory-grounded, evidence-verifiable Teacher-in-the-Loop evaluation pipeline on controlled classroom transcripts.

## Research objective

To investigate whether a theory-grounded, evidence-verifiable Teacher-in-the-Loop evaluation pipeline improves agreement with human pedagogical judgments and reduces unsupported feedback compared with a generic LLM evaluator.

## Phase 1 scope

Phase 1 creates the research foundation:

- protocol documents
- golden benchmark folder structure
- SQLite schema
- reproducibility metadata
- threats to validity
- schema validation tests

## Repository layout

```text
frontend/      # React/Vite UI, added in Phase 2
backend/       # FastAPI/research backend
docs/          # benchmark, rubric, reproducibility, validity docs
```

## Current status

Phase 1 complete. Phase 2 complete with a working FastAPI + React/Vite pixel classroom demo. Phase 3 complete with provider-agnostic evaluator, deterministic evidence verification, and blinded review UI. Phase 4 MVP complete with batch runner, metrics, CSV/SVG exports, and reproducibility manifest.

## Run Phase 2 demo

Backend:

```bash
cd D:/Code/til-classroom-sim/backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd D:/Code/til-classroom-sim/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

## Run Phase 3/4 evaluation pipeline

Configure evaluator provider in local `.env`:

```text
EVALUATOR_PROVIDER=fallback # or openai, anthropic, gemini, openai_compatible
EVALUATOR_MODEL=deterministic-fallback
EVALUATOR_API_KEY=
```

Run backend tests:

```bash
cd D:/Code/til-classroom-sim/backend
uv run pytest -q
```

Run a Phase 4 benchmark/export:

```bash
cd D:/Code/til-classroom-sim/backend
uv run python -m scripts.run_benchmark --conditions baseline,til --repetitions 1 --transcript-id python_loops_weak_001
```

Exports are written by default under:

```text
D:/Mythesis(Honours)/thesis-project/results
```
