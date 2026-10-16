# Scenario Academic Accuracy Notes

This note records the disciplinary knowledge sources used to rewrite and verify the 8 fixed 30-minute classroom transcript scenarios. The scenarios are still editable benchmark fixtures, not textbook substitutes, but the core explanations and worked examples were aligned with standard university/open-textbook concepts.

## Global structural constraints

- 8 scenarios total.
- Exactly 64 transcript turns per scenario.
- 30-minute timestamps preserved (`0`–`30`).
- Required parts preserved in transcript text:
  1. `PART 1 — INTRODUCTION`
  2. `PART 2 — CONCEPT EXPLANATION`
  3. `PART 3 — QUICK CHECK`
  4. `PART 4 — WORKED EXAMPLE`
  5. `PART 5 — DIFFERENTIATED PRACTICE`
  6. `PART 6 — MISCONCEPTION REPAIR`
  7. `PART 7 — FINAL REVIEW`
- English-name roster preserved: `Mr. Anderson`, `Alice`, `Ben`, `Chloe`, `Daniel`, `Lily`, `Noah`.
- Pedagogical tags and timestamps are generated from the canonical 64-turn skeleton in `backend/app/transcript_service.py`.
- Current dialogue style target: teacher-led realistic classroom discourse, approximately 1,800–2,100 words per scenario, with about 65–75% teacher words and only a few genuine student questions while still preserving observable quick-check, worked-example, misconception-repair, differentiated-practice, and final-review evidence.

## Source basis by scenario

### Python for-loops

Source basis:
- Python documentation — control flow / `for` statements and `range`: https://docs.python.org/3/tutorial/controlflow.html
- Python documentation — iterator types / iterator protocol: https://docs.python.org/3/library/stdtypes.html#iterator-types
- Python data model — `object.__iter__` and iterator protocol hooks: https://docs.python.org/3/reference/datamodel.html#object.__iter__
- Runestone Academy / Foundations of Python Programming — accumulator pattern: https://runestone.academy/ns/books/published/fopp/Iteration/TheAccumulatorPattern.html

Accuracy checks:
- Python `for` loops iterate by obtaining values from an iterable/iterator rather than acting as C-style manual counter loops.
- The iterator protocol is based on obtaining an iterator and repeatedly requesting the next value until exhaustion.
- `range(stop)` excludes the stop value, so `range(3)` yields `0, 1, 2`.
- `enumerate(iterable)` yields index/value pairs that can be unpacked into multiple loop targets.
- Indentation controls whether a statement is inside or outside the loop body.
- State tracing and accumulator invariants are valid pedagogical methods for reasoning about variable bindings, outputs, side effects, boundary cases, and correctness.

### Quadratic functions

Source basis:
- OpenStax College Algebra 2e — Quadratic Functions: https://openstax.org/books/college-algebra-2e/pages/5-1-quadratic-functions

Accuracy checks:
- `a` determines whether a parabola opens upward or downward.
- `x = -b/(2a)` gives the axis of symmetry for `ax^2 + bx + c`.
- The vertex is a minimum if `a > 0` and a maximum if `a < 0`.
- `c` is the y-intercept, not automatically an x-intercept.
- The discriminant `b^2 - 4ac` identifies the number/type of real zeros.
- Completing the square exposes vertex form `a(x-h)^2 + k`.

### Newton's laws of motion

Source basis:
- OpenStax University Physics Vol. 1 — Chapter 5 Summary: https://openstax.org/books/university-physics-volume-1/pages/5-summary
- OpenStax University Physics Vol. 1 — Newton's Second Law: https://openstax.org/books/university-physics-volume-1/pages/5-3-newtons-second-law

Accuracy checks:
- Newton's first law applies in inertial reference frames.
- Constant velocity means zero net external force, not necessarily no forces.
- `F = ma` uses net external force.
- Free-body diagrams must include only forces acting on the selected object.
- Third-law force pairs are equal/opposite but act on different bodies/systems, so they do not cancel in one object's force sum.

### Cellular respiration

Source basis:
- OpenStax Biology 2e — Oxidative Phosphorylation: https://openstax.org/books/biology-2e/pages/7-4-oxidative-phosphorylation
- OpenStax Biology 2e — Cellular Respiration chapter overview: https://openstax.org/books/biology-2e/pages/7-introduction

Accuracy checks:
- Cellular respiration is a redox energy-transfer pathway, not energy creation from nothing.
- NADH and FADH2 carry electrons to the electron transport chain.
- Electron transport drives proton pumping and builds a proton-motive force.
- Chemiosmosis couples proton flow through ATP synthase to ATP production.
- Oxygen acts as terminal electron acceptor in aerobic respiration.
- Fermentation regenerates NAD+ without oxidative phosphorylation.

### Stoichiometry and limiting reagents

Source basis:
- OpenStax Chemistry 2e — Reaction Stoichiometry: https://openstax.org/books/chemistry-2e/pages/4-3-reaction-stoichiometry
- OpenStax Chemistry 2e — Reaction Yields: https://openstax.org/books/chemistry-2e/pages/4-4-reaction-yields

Accuracy checks:
- Stoichiometric coefficients express mole ratios.
- Masses must be converted to moles before coefficient ratios are used.
- The limiting reagent is consumed first and determines theoretical yield.
- Percent yield compares actual yield with theoretical yield.
- Smaller mass is not automatically the limiting reagent.

### Hypothesis testing

Source basis:
- OpenIntro Statistics / inference materials: https://www.openintro.org/book/os/
- OpenIntro/LibreTexts hypothesis testing overview: https://stats.libretexts.org/Bookshelves/Introductory_Statistics/OpenIntro_Statistics_(Diez_et_al)./04:_Foundations_for_Inference/4.04:_Hypothesis_Testing

Accuracy checks:
- A p-value is computed under the null model; it is not the probability that the null hypothesis is true.
- Decision rule compares p-value with alpha.
- A Type I error is rejecting a true null hypothesis.
- Statistical significance is distinct from practical importance.
- Effect size and confidence intervals are needed for substantive interpretation.
- Failing to reject the null does not prove zero effect.

### Price elasticity of demand

Source basis:
- OpenStax Principles of Economics 3e — Price Elasticity of Demand and Supply: https://openstax.org/books/principles-economics-3e/pages/5-1-price-elasticity-of-demand-and-price-elasticity-of-supply
- OpenStax Principles of Economics 3e — Elasticity and Pricing: https://openstax.org/books/principles-economics-3e/pages/5-3-elasticity-and-pricing

Accuracy checks:
- Elasticity is a unit-free ratio of percentage changes.
- The midpoint formula uses average price/quantity bases and avoids direction bias.
- Elasticity is not the same as slope.
- Total revenue effects depend on whether demand is elastic or inelastic over the relevant range.
- Availability of substitutes, necessity, budget share, and time horizon affect elasticity.

### Primary source analysis

Source basis:
- Digital Inquiry Group / Stanford History Education Group — Historical Thinking Chart: https://www.inquirygroup.org/history-lessons/historical-thinking-chart

Accuracy checks:
- Primary sources are evidence from the period, not automatically objective truth.
- Sourcing asks who created the source, when, for whom, and why.
- Contextualization places the source in historical setting and purpose.
- Corroboration checks claims against other sources.
- Historical claims should explain limits of what one excerpt can prove.

## Verification commands

Recommended checks after scenario edits:

```bash
cd D:/Code/til-classroom-sim/backend
uv run python -m pytest tests/test_transcript_system.py -q
uv run python -m pytest -q
cd ../frontend
export PATH='/c/Program Files/nodejs':"$PATH" && npm run build
```
