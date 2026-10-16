# System Architecture

## Research pipeline

```text
Scenario Definition
        ↓
Golden Benchmark Transcript
        ↓
Immutable Transcript
        ↓
┌────────────────────────────────────┐
│ Condition A: Generic Evaluator     │
│ Condition B: TIL Grounded Evaluator│
└────────────────────────────────────┘
        ↓
Evidence Verification Layer
        ↓
Blinded Human Review
        ↓
Research Dataset
        ↓
Statistical Analysis
        ↓
CSV Exports + Charts / Thesis Figures
```

## Application layers

```text
React/Vite Pixel UI
  ├─ Interactive classroom demo
  ├─ Golden benchmark selection
  └─ Blinded feedback review

FastAPI/Python backend
  ├─ SQLite metadata store
  ├─ Golden benchmark loader
  ├─ OpenAI evaluator runner
  ├─ Evidence verifier
  ├─ Blinding service
  └─ Export/metrics scripts
```

## Phase 1 implementation focus

Phase 1 builds only the research foundation:

- docs;
- SQLite schema;
- golden benchmark seed files;
- schema validation tests.
