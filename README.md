## Teacher-in-the-Loop Agentic AI for
Evidence-Grounded Pedagogical Feedback

This repository contains the PixelClass TIL implementation and the frozen
transcript benchmark used in Thanh Y Nguyen's Bachelor of Computer Science
(Honours) thesis at Griffith University, supervised by Dr. Thanh Tam Nguyen.

The experiment compares generic structured teaching feedback with TIL-EGE:
rubric guidance and explicit links between feedback claims and transcript turns.
The verifier checks stored quotation-turn pairs. Score agreement compares model
scores with the benchmark references.

## Contents

| Path | Contents |
| --- | --- |
| backend/app/ | FastAPI application, evaluator adapters, verifier, review and metrics |
| backend/prompts/ | Evaluator, student and verifier prompt resources |
| backend/data/golden_benchmark_real_v0/ | Six anonymised observed transcripts and final labels |
| backend/data/golden_benchmark_expanded/ | Sixteen curated transcripts and labels |
| frontend/ | React/Vite classroom and review interface |
| dataset/ | Catalogue of the 22 thesis transcripts, source links and integrity hashes |
| docs/ | Benchmark, rubric and review documentation |
| src/ | Earlier conceptual simulator retained from the original repository |

The older numbered documents under docs/ describe the conceptual simulator.
The thesis experiment uses backend/ and the two benchmark folders listed above.

## Install and run

Use Python 3.10 or newer and Node.js with npm. From the repository root:

```bash
cd backend
uv sync
uv run python -m app.seed_data
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open the local address printed by Vite. Runtime data and exports stay in this
checkout by default. THESIS_PROJECT_ROOT and EXPORT_ROOT can override the paths.

## Check the benchmark

From backend/:

```bash
uv run python -m scripts.verify_thesis_dataset
uv run python -m app.seed_data
uv run pytest -q
```

A deterministic benchmark run needs no API key:

```bash
uv run python -m scripts.run_benchmark --benchmark-root data/golden_benchmark_expanded --conditions baseline,til --repetitions 1
```

For the six observed transcripts, use
--benchmark-root data/golden_benchmark_real_v0 instead.

## Live providers and historical results

Live evaluation supports OpenAI, Anthropic, Gemini and compatible endpoints.
Configure provider, model and credentials locally through environment variables
or a private .env file. No environment file or credential is distributed here.

The code is the available implementation snapshot. Its current output normaliser
selects the first three valid items. The thesis analyses every item saved in the
historical selected runs, including longer responses; it does not apply that later
selection rule retrospectively. Re-running a provider creates a new stochastic
sample. Historical output files remain in the thesis supplementary archive.

API credentials, assistant working files, conversation logs, provider outputs,
audio, video, dependency folders and build products are excluded from this upload.
