# PixelClass TIL Expanded Golden Benchmark

Dataset version: `golden_benchmark_expanded_v1.1_transcript_scenarios`

This folder is generated from the transcript-first scenario library.
Each scenario contains a researcher-authored strong teaching variant and a deliberately weak variant.

## Claim boundary

Researcher-authored synthetic benchmark transcripts; suitable for controlled evaluator comparison, not evidence of real classroom learning gains.

## Included scenarios

- `college_cellular_respiration_30m` — Cellular respiration: ATP production and energy transfer (Biology, college); strong=`college_cellular_respiration_30m_strong_001`, weak=`college_cellular_respiration_30m_weak_001`
- `college_stoichiometry_30m` — Stoichiometry: mole ratios and limiting reactants (Chemistry, college); strong=`college_stoichiometry_30m_strong_001`, weak=`college_stoichiometry_30m_weak_001`
- `hs_newton_laws_30m` — Newtonian mechanics: free-body diagrams, net force, and system boundaries (Physics, college); strong=`hs_newton_laws_30m_strong_001`, weak=`hs_newton_laws_30m_weak_001`
- `hs_python_loops_30m` — Python for-loops: iterator protocol, tracing, and correctness reasoning (Computer Science, college); strong=`hs_python_loops_30m_strong_001`, weak=`hs_python_loops_30m_weak_001`
- `hs_quadratic_functions_30m` — Quadratic functions: structural forms, discriminant, and modelling interpretation (Mathematics, college); strong=`hs_quadratic_functions_30m_strong_001`, weak=`hs_quadratic_functions_30m_weak_001`
- `uni_hypothesis_testing_30m` — Hypothesis testing: p-values, significance, and interpretation (Statistics, university); strong=`uni_hypothesis_testing_30m_strong_001`, weak=`uni_hypothesis_testing_30m_weak_001`
- `uni_microeconomics_elasticity_30m` — Microeconomics: price elasticity and revenue reasoning (Economics, university); strong=`uni_microeconomics_elasticity_30m_strong_001`, weak=`uni_microeconomics_elasticity_30m_weak_001`
- `uni_primary_source_analysis_30m` — Primary source analysis: evidence, context, and historical claims (History / Humanities, university); strong=`uni_primary_source_analysis_30m_strong_001`, weak=`uni_primary_source_analysis_30m_weak_001`

## Run benchmark

```bash
cd D:/Code/til-classroom-sim/backend
EVALUATOR_PROVIDER=fallback EVALUATOR_MODEL=deterministic-fallback uv run python -m scripts.run_benchmark --benchmark-root data/golden_benchmark_expanded --conditions baseline,til --repetitions 3
```

For a real LLM experiment, configure one provider/model in `.env`, keep temperature fixed, and run the same command without overriding the provider to fallback.
