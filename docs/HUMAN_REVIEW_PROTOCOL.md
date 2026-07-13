# Human Review Protocol

## Purpose

Human review provides comparison data for evaluating baseline and TIL evaluator outputs.

## Reviewer roles

Preferred:

- two educators or teaching-experienced reviewers;
- independent review;
- disagreement adjudication.

If not available:

- use researcher annotation;
- label results as researcher annotation, not expert validation.

## Blinding

Reviewers must see only:

- `Evaluation A`
- `Evaluation B`

They must not see:

- `baseline`
- `til_grounded`

until the review is complete.

## Per-feedback-item annotation fields

Each feedback item should be annotated with:

- accept/reject claim;
- human score 1–5 if relevant;
- usefulness 1–5;
- fabricated evidence flag;
- unsupported inference flag;
- pedagogical disagreement flag;
- missed issue flag;
- optional comment;
- review time in seconds.

## Error definitions

### Fabricated evidence

The evaluator quotes or references a transcript statement that does not exist.

### Unsupported inference

The quoted evidence exists, but the evaluator's interpretation goes beyond what the evidence supports.

### Pedagogical disagreement

The evidence exists, but the pedagogical scoring or interpretation differs from human judgement.
