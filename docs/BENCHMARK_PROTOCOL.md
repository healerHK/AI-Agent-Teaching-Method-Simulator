# Benchmark Protocol

## Research objective

To investigate whether a theory-grounded, evidence-verifiable Teacher-in-the-Loop evaluation pipeline improves agreement with human pedagogical judgments and reduces unsupported feedback compared with a generic LLM evaluator.

## Benchmark design

The benchmark uses fixed golden classroom transcripts. Each transcript has ground truth files so the same transcript can be evaluated by multiple evaluator conditions.

```text
Golden transcript
  -> Baseline evaluator
  -> TIL grounded evaluator
  -> Evidence verifier
  -> Human/researcher annotation
  -> Metrics
```

## Minimum Phase 1 dataset

Phase 1 includes one scenario:

- `python_loops`

With two teacher-performance variants:

- `strong`
- `weak`

## Full pilot target

```text
10 scenarios × 2 variants = 20 transcripts
20 transcripts × 2 evaluator conditions × 3 repetitions = 120 evaluator outputs
```

## Evaluator conditions

1. **Baseline evaluator**: generic LLM feedback without detailed rubric grounding.
2. **TIL grounded evaluator**: rubric-based, evidence-linked evaluator requiring claim, criterion, score, evidence turn IDs, evidence quotes, suggested action, and confidence.

## Primary outcomes

- Human agreement with rubric scores.
- Fabricated evidence rate.
- Unsupported inference rate.
- Pedagogical disagreement rate.
- Missed pedagogical opportunity precision/recall/F1.

## Blinding

Human reviewers see `Evaluation A` and `Evaluation B`, not the actual evaluator condition. Backend stores the condition mapping and reveals it only after review is complete.
