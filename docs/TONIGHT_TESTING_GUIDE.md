# Tonight Testing Guide — PixelClass TIL

This guide is for testing the thesis MVP tonight without exposing API keys.

## 1. Current testing target

Project: **Teacher-in-the-Loop Agentic AI for Pedagogically Grounded Multi-Agent Classroom Simulation**

MVP capabilities ready for testing:

- 2D pixel classroom demo with teacher input and virtual student replies.
- Golden benchmark transcript evaluation.
- Baseline vs Teacher-in-the-Loop evaluator comparison.
- Evidence verification that checks cited turn IDs and quotes.
- Blinded A/B review UI.
- Human annotation saving.
- Phase 4 benchmark runner with CSV/SVG exports and reproducibility manifest.
- Provider-agnostic evaluator config with Gemini/OpenAI/Claude/OpenAI-compatible/fallback support.

## 2. Gemini status

Local `.env` should use this shape:

```text
EVALUATOR_PROVIDER=gemini
EVALUATOR_MODEL=gemini-2.5-flash
EVALUATOR_API_KEY=your_gemini_key
GEMINI_FALLBACK_MODELS=gemini-flash-latest
EVALUATOR_TEMPERATURE=0.2
```

The app never commits or prints the key. `/api/evaluator/status` only reports whether a key is configured.

If live Gemini returns `403 PERMISSION_DENIED`, the code is configured but the Google key/project does not have generation permission. Testing can still continue because the evaluator falls back to deterministic evidence-grounded output.

Checklist if Gemini returns 403:

1. Create/verify an API key from Google AI Studio: `https://aistudio.google.com/app/apikey`
2. Confirm the key belongs to a project allowed to use the Gemini API.
3. Confirm the key is not restricted away from the Generative Language API.
4. Replace only the local `.env` key; do not commit it.
5. Re-run the live smoke command below.

## 3. One-command testing pack

From Git Bash:

```bash
cd D:/Code/til-classroom-sim/backend
uv run python -m scripts.testing_pack --live-provider-smoke
```

Expected result:

- Prints safe provider status.
- Prints Gemini live-smoke status as either:
  - `status: ok`, or
  - `failed_provider_http` with `fallback_available: true`.
- Runs baseline and TIL on `python_loops_weak_001`.
- Verifies evaluator evidence.
- Exports CSV/SVG/manifest to `D:/Mythesis(Honours)/thesis-project/results/...`.

## 4. Backend checks

```bash
cd D:/Code/til-classroom-sim/backend
uv run pytest -q
uv run python -m scripts.testing_pack
```

Optional API server:

```bash
cd D:/Code/til-classroom-sim/backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Smoke endpoints:

```bash
curl -fsS http://127.0.0.1:8000/api/health
curl -fsS http://127.0.0.1:8000/api/evaluator/status
```

## 5. Frontend checks

```bash
cd D:/Code/til-classroom-sim/frontend
export PATH='/c/Program Files/nodejs':"$PATH"
npm run build
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

Manual test flow:

1. Confirm the start screen shows **Tonight testing status**.
2. Click **Run Live Pixel Classroom Demo**.
3. Send one teacher message.
4. Confirm student replies appear and transcript grows.
5. Reset.
6. Click **Evaluate Golden Benchmark**.
7. Confirm blinded Evaluation A/B cards appear.
8. Confirm one side has stronger verified evidence than the generic baseline.
9. Click Accept/Reject on at least one item.
10. Confirm no browser console errors.

## 6. Testing notes for thesis reporting

For tonight, the key claim is not that Gemini always succeeds. The stronger research claim is:

- The pipeline records provider configuration.
- Provider failure is explicit and redacted.
- The deterministic Teacher-in-the-Loop fallback remains evidence-grounded.
- Evidence verification catches unsupported/fabricated feedback.
- Blinded review and annotation are usable for human evaluation.

Use the exported CSV/SVG/manifest files as reproducibility artifacts.
