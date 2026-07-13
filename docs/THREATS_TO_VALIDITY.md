# Threats to Validity

Threats to validity are part of the design from Phase 1, not an afterthought.

## Internal validity

Threats:

- The same LLM family may be used for simulation and evaluation.
- Prompt wording may influence outputs beyond the intended rubric design.
- Repeated runs may vary due to nondeterministic API behavior.
- Reviewers may infer the evaluator condition over time.

Mitigations:

- Use fixed golden benchmark transcripts.
- Use the same transcript for both evaluator conditions.
- Store prompt/model/version metadata for every run.
- Blind evaluator labels as Evaluation A/B.
- Report repeated-run stability.

## Construct validity

Threats:

- The five rubric dimensions may not capture all teacher expertise.
- Human annotation may contain bias.
- Researcher annotation is not expert validation.
- Deterministic evidence verification confirms quote existence, not full pedagogical meaning.

Mitigations:

- Define rubric dimensions before experiments.
- Store ground truth files per transcript.
- Use educator reviewers if possible.
- Separate fabricated evidence, unsupported inference, and pedagogical disagreement.

## External validity

Threats:

- Only introductory CS may not generalise to mathematics, science, humanities, or secondary education.
- Synthetic transcripts may not represent real classroom complexity.
- Pixel UI demo sessions may not generalise to real teacher-training environments.
- One OpenAI model may not generalise to other LLM providers or future versions.

Mitigations:

- Prefer a balanced benchmark across CS, mathematics, and science when time allows.
- If scoped to introductory CS, state this limitation clearly.
- Avoid claims about real learning gains.
- Report model name/version for all results.

## Conclusion validity

Threats:

- The pilot dataset may be small.
- A small number of reviewers limits reliability.
- Multiple metrics can encourage overinterpretation.
- Failed API runs may bias results if hidden.

Mitigations:

- Treat results as pilot evidence.
- Report failed runs and exclusions.
- Use repeated runs.
- Focus conclusions on agreement and evidence validity, not real learning outcomes.
