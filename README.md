# AI Agent Teaching Method Simulator

## Project Overview

**AI Agent Teaching Method Simulator** is a simulation framework designed to evaluate various teaching methods using Generative Agents. This project models virtual students and teachers to simulate classroom interactions and measure the effectiveness of different instructional strategies.

### Teaching Methods Supported
- Flipped Classroom
- Direct Instruction
- Inquiry-Based
- Problem-Based
- Project-Based
- Collaborative Learning
- Game-based

### What Problem Does This Project Solve?

Traditionally, testing new teaching methods requires:
- Real students and real classrooms
- Significant time commitments
- Ethics approval
- Risk of ineffective interventions

This simulator provides:
- Cost-free, risk-free, reproducible educational method analysis
- Scalable cohorts of virtual students with diverse profiles (motivation, prior knowledge, personality)
- Metrics-driven comparisons of instructional approaches—before real-world trials

---

## Analysis: Goals and Scope

This repository places emphasis on analysis of simulation outputs to answer empirical and practical questions such as:

- Which methods maximize short-term learning gains vs. long-term retention?
- How do methods perform for different learner profiles (motivation, prior knowledge, learning style)?
- What trade-offs exist between engagement and misconception reduction?
- How sensitive are outcomes to variations in teacher policy or material difficulty?

Analysis scope includes:
- Pre/post test score changes and effect sizes (Cohen's d)
- Misconception reduction and confidence calibration
- Engagement and participation metrics
- Variance and robustness across stochastic runs
- Subgroup analysis by student profile (e.g., low/high prior knowledge, motivation levels)

Statistical methods and considerations:
- Use Cohen's d or other effect-size measures for educational impact
- Bootstrap or permutation tests for non-parametric CI estimates
- Linear mixed-effects models or hierarchical models for repeated measures and nested data (students within runs)
- Multiple comparisons correction for pairwise method comparisons
- Sensitivity analyses (vary seeds, teacher policies, difficulty)

---

## Repository Structure

```
teaching-method-simulator/
│
├── README.md                          # Project overview and instructions
│
├── docs/                              # Documentation files
│   ├── 01_introduction.md             # Project introduction and background
│   ├── 02_literature_review.md        # References and prior work
│   ├── 03_proposed_framework.md       # Technical and conceptual framework
│   ├── 04_simulation_workflow.md      # Simulation workflow and logic
│   ├── 05_metrics_evaluation.md       # Metrics definition and evaluation strategies
│   ├── 06_limitations_future_work.md  # Limitations and future directions
│   └── diagram_simulation_workflow.png
│
├── src/                               # Source code and modules
│   ├── agents/                        # Generative agent implementations
│   │   ├── student_agent.py
│   │   ├── teacher_agent.py
│   │   └── memory_module.py
│   ├── teaching_methods/              # Teaching strategies
│   │   ├── flipped_classroom.py
│   │   ├── direct_instruction.py
│   │   ├── inquiry_based.py
│   │   ├── problem_based.py
│   │   ├── project_based.py
│   │   └── collaborative.py
│   ├── simulation/                    # Simulation mechanics and metrics evaluation
│   │   ├── environment.py
│   │   ├── run_simulation.py
│   │   └── evaluate_metrics.py
│   └── utils/                         # Helper utilities and configuration
│       ├── logging.py
│       ├── data_structures.py
│       └── config.py
│
├── data/                              # Datasets and experimental results
│   ├── learning_materials/
│   │   ├── physics_intro.txt
│   │   └── sample_videos/
│   └── results/
│       └── experiment_01.json
│
└── LICENSE                            # MIT License
```
---

## Metrics (examples)

Each experiment run should output these (or a superset) in per-run JSONs:

- avg_pretest: mean pre-test score
- avg_posttest: mean post-test score
- gain_score: avg_posttest - avg_pretest
- effect_size: Cohen's d (post vs pre, or between-method comparisons)
- misconception_reduction: fraction (e.g., proportion of corrected misconceptions)
- engagement_score: normalized 0–1 measure (participation, responsiveness)
- retention_estimate: modeled retention (e.g., decay model parameter or predicted score after T days)
- participation_rate: fraction of active participants
- question_quality_score: proxy for depth of student questions
- time_on_task: average time spent on learning activities
- cognitive_load_index: if modeled (subjective/estimated)

Suggested output format (per-run JSON):
```json
{
  "method": "Flipped Classroom",
  "seed": 42,
  "n_students": 50,
  "avg_pretest": 45.2,
  "avg_posttest": 72.1,
  "gain_score": 26.9,
  "effect_size": 1.02,
  "misconception_reduction": 0.41,
  "engagement_score": 0.82,
  "participation_rate": 0.78,
  "retention_estimate": 0.65,
  "time_on_task": 37.4
}
```

File naming convention recommendation:
- data/results/{method_slug}_seed{SEED}.json
- e.g., data/results/flipped_classroom_seed42.json

---

## Analysis Workflow

1. Design experiments and set reproducible parameters in src/utils/config.py (method parameters, seeds, student profile distributions, run counts).
2. Run N simulation replicates per condition with fixed seeds and varied student profiles:
   - src/simulation/run_simulation.py — driver to run experiments and write per-run JSON outputs to data/results/.
3. Collect per-run JSON results into data/results/.
4. Aggregate runs and compute summary statistics (mean, median, 95% CI, variance).
   - src/simulation/evaluate_metrics.py — aggregator and metrics calculator.
5. Compute effect sizes and perform subgroup comparisons (e.g., by prior knowledge, motivation).
6. Visualize results:
   - Pre/post distributions (violin/box plots)
   - Gain histograms
   - Metric time-series (per-step or per-session)
   - Spider/radar plots comparing methods across multiple metrics
   - Robustness plots: outcome vs. teacher policy or material difficulty
7. Report:
   - Tables for methods (aggregate metrics)
   - Detailed per-profile comparisons (subgroup tables/figures)
   - Robustness checks and sensitivity analysis
8. Save aggregated outputs and figures to a results/analysis subfolder for reproducibility and dissemination.

Reproducibility best practices:
- Fix random seeds per-run and record them in outputs
- Version-control config files and analysis notebooks
- Store raw per-run JSONs and aggregated summaries separately

---

## Scripts (Example)

- src/simulation/run_simulation.py
  - Driver that:
    - loads an experiment configuration,
    - generates student cohorts (with profile distributions),
    - runs a teaching-method simulation for each replicate,
    - writes per-run JSON outputs to data/results/.
  - CLI options: --method, --n-students, --n-replicates, --seed, --out-dir

- src/simulation/evaluate_metrics.py
  - Aggregates per-run JSON files,
  - Computes summary statistics (mean, median, CI),
  - Computes effect sizes (Cohen's d) and subgroup comparisons,
  - Produces CSV/JSON summary outputs and optionally basic plots.

- src/utils/config.py
  - Central experiment parameter definitions:
    - default seeds, method hyperparameters, student profile templates, run counts, output paths

- analysis/ (Optional we can do later)
  - Jupyter notebooks for exploratory analysis and statistical tests:
    - analysis/01_aggregate_and_describe.ipynb
    - analysis/02_visualizations.ipynb
    - analysis/03_statistical_tests.ipynb

- src/utils/logging.py
  - Standardized logging for experiments and reproducibility

Example CLI usage (conceptual):
```bash
python src/simulation/run_simulation.py --method flipped_classroom --n-students 50 --n-replicates 30 --seed 42 --out-dir data/results/
python src/simulation/evaluate_metrics.py --input-dir data/results/ --output data/analysis/summary.csv
```

---

## Visualizations & Reporting Suggestions

- Per-method dashboards showing:
  - Pre/post-test distribution (violin + box)
  - Gain score histogram and density
  - Engagement vs. misconception scatter with regression lines
  - Radar charts across key metrics (engagement, gain, misconception_reduction, retention)
- Robustness checks:
  - Plot metrics vs. teacher_policy parameter sweep
  - Plot outcome variance across seeds
- Save figures to results/figures/ with descriptive filenames for reproducibility

---

## Example Files to Seed Repository

- docs/04_simulation_workflow.md — include the PNG diagram and narrative workflow
- src/agents/student_agent.py — minimal StudentAgent skeleton
- src/teaching_methods/flipped_classroom.py — skeleton implementation
- src/simulation/run_simulation.py — experimental driver (skeleton)
- src/simulation/evaluate_metrics.py — aggregator (skeleton)
- src/utils/config.py — default parameters and seed list
- data/results/experiment_01.json — example run output 

---

## Final Notes

This analysis-first organization helps ensure the repository not only contains simulation code but also the necessary components for rigorous evaluation, reproducibility, and academic presentation.

