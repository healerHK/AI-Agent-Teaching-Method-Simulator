# Reproducibility Protocol

## Goal

Every experiment output must be traceable to the exact dataset, transcript, prompt, rubric, model, code version, and timestamp used to generate it.

## Experiment ID

Use this format:

```text
exp_YYYYMMDD_HHMMSS_<short_uuid>
```

Example:

```text
exp_20260713_153012_a8f3
```

## Required metadata

Every evaluator run stores:

- experiment ID;
- dataset version;
- transcript ID;
- scenario ID;
- evaluator condition;
- prompt version;
- rubric version;
- OpenAI model;
- temperature;
- seed if available;
- git commit hash;
- dirty working tree flag;
- timestamp started;
- timestamp completed;
- latency;
- input tokens;
- output tokens;
- estimated cost;
- raw response path;
- verifier version;
- metrics script version.

## Dataset version file

Dataset version lives at:

```text
backend/data/golden_benchmark/DATASET_VERSION.json
```

## Export manifest

Each experiment export must include:

```text
reproducibility_manifest.json
```

The manifest is the canonical record for reproducing or auditing a run.
