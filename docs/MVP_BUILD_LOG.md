# MVP Build Log

## 2026-07-13 — Phase 1 Research Foundation

### Completed

- Created local repo at `D:/Code/til-classroom-sim`.
- Added research protocol documents:
  - `docs/BENCHMARK_PROTOCOL.md`
  - `docs/EVALUATION_RUBRIC.md`
  - `docs/HUMAN_REVIEW_PROTOCOL.md`
  - `docs/REPRODUCIBILITY_PROTOCOL.md`
  - `docs/THREATS_TO_VALIDITY.md`
  - `docs/SYSTEM_ARCHITECTURE.md`
  - `docs/DESIGN.md`
- Implemented backend Phase 1 foundation:
  - `backend/app/config.py`
  - `backend/app/models.py`
  - `backend/app/database.py`
  - `backend/app/migrations.py`
  - `backend/app/seed_data.py`
- Created Phase 1 golden benchmark dataset:
  - `backend/data/golden_benchmark/DATASET_VERSION.json`
  - `backend/data/golden_benchmark/python_loops/scenario.json`
  - `backend/data/golden_benchmark/python_loops/strong/*`
  - `backend/data/golden_benchmark/python_loops/weak/*`
- Added tests for:
  - SQLite schema
  - golden benchmark schema
  - reproducibility manifest model
  - database seeding idempotency

### Verification

Command:

```bash
cd D:/Code/til-classroom-sim/backend
uv run pytest -q
```

Result:

```text
11 passed in 0.43s
```

Seed verification:

```text
tables 12
scenarios 1
golden_items 2
turns 18
```

### Git

Initial Phase 1 commit:

```text
314b23e feat: establish phase 1 research foundation
```

Runtime/ignored files confirmed ignored:

```text
backend/.venv/
backend/.pytest_cache/
backend/data/til_research.db
__pycache__/
```

## 2026-07-13 — Phase 2 Interactive Pixel Classroom Demo

### Completed

- Added FastAPI app at `backend/app/main.py`.
- Added deterministic classroom session controller at `backend/app/session_controller.py`.
- Added optional OpenAI-backed student response client with fallback mode at `backend/app/openai_client.py`.
- Added runtime session models at `backend/app/session_models.py`.
- Added student simulation prompt at `backend/prompts/students/v1.txt`.
- Added React/Vite frontend under `frontend/`.
- Built pixel classroom UI with:
  - teacher character;
  - five student characters;
  - learning objective board;
  - dialogue bubble;
  - teacher input panel;
  - transcript panel;
  - session metadata panel.

### Verification

Backend tests:

```text
15 passed in 0.89s
```

Backend health endpoint:

```text
GET /api/health
{"status":"ok","phase":"phase_2_interactive_demo"}
```

Frontend build:

```text
npm run build
✓ built in 140ms
```

Browser verification:

- Opened `http://127.0.0.1:5173`.
- Started a live pixel classroom session.
- Sent a teacher message.
- Verified transcript contained teacher turn plus Alex and Mia student replies.
- Verified UI showed fallback source when no OpenAI key is required.

## 2026-07-17 — Phase 3 Evaluation Pipeline + Phase 4 MVP Batch Experiments

### Completed

- Added provider-agnostic evaluator client supporting `fallback`, `openai`, `anthropic`, `gemini`, and `openai_compatible`.
- Added local `.env` loader with committed `.env.example` only.
- Added baseline and TIL evaluator prompts.
- Added golden benchmark loader.
- Added evaluation runner and raw output storage.
- Added deterministic evidence verifier.
- Added blinded A/B review service.
- Added human annotation service and endpoint.
- Added frontend blinded review UI.
- Added Phase 4 batch runner, metrics service, export service, CSV outputs, SVG charts, and reproducibility manifest.

### Verification

Backend tests:

```text
21 passed in 0.96s
```

Frontend build:

```text
npm run build
✓ built in 121ms
```

Phase 4 smoke export:

```text
D:/Mythesis(Honours)/thesis-project/results/exp_20260717_075258_d0d6
```

Browser verification:

- Opened `http://127.0.0.1:5173`.
- Clicked `Evaluate Golden Benchmark`.
- Verified Blinded Evaluation A/B UI rendered.
- Verified baseline showed missing evidence and TIL showed verified evidence.
- Saved one annotation through the UI and verified count changed to `1`.

Provider smoke test:

- Local `.env` configured for Gemini 2.5 Flash.
- Provider call returned sanitized HTTP 403.
- Pipeline fell back safely and still produced verified TIL evidence.
