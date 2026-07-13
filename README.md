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

Phase 1 complete. Phase 2 complete with a working FastAPI + React/Vite pixel classroom demo.

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
