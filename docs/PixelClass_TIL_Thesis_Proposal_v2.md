# PixelClass TIL Thesis Proposal v2

**Working title:** PixelClass TIL: A Teacher-in-the-Loop Benchmark System for Evaluating Pedagogical Feedback in Simulated Classroom Teaching Sessions  
**Student:** Thành Ý  
**Project repository:** https://github.com/healerHK/AI-Agent-Teaching-Method-Simulator  
**Current implementation branch:** `pixelclass-til-v2-mvp`  
**Current implementation commit:** `007cff5`  
**Generated:** 2026-07-27 19:48 EAST  
**Purpose of this document:** This proposal records the complete thesis direction, research framing, MVP architecture, methodology, evaluation protocol, claim guardrails, and next development plan so that the project can be resumed later without losing context.

---

## Vietnamese quick handoff for future recall

Đề tài hiện tại không còn nên được hiểu là chỉ “build một AI classroom simulation demo”. Hướng đúng và dễ bảo vệ hơn là:

**PixelClass TIL is a Teacher-in-the-Loop, evidence-grounded benchmark system for evaluating pedagogical feedback in simulated classroom teaching sessions.**

Nói ngắn gọn:

- **Simulation is the testbed.** Pixel classroom và AI student agents dùng để tạo/kiểm soát teaching transcripts.
- **Evaluation is the contribution.** Luận văn chính yếu kiểm tra liệu TIL evaluator có feedback evidence-grounded, actionable, ít unsupported claims, và aligned hơn với expert pedagogical judgement so với generic LLM baseline hay không.
- **Live Mode is supportive.** Live mode dùng cho demo/pilot/usability và lấy exploratory human-teacher transcript, không phải benchmark chính.
- **Transcript Benchmark Mode is the main research path.** Fixed/frozen transcripts giúp so sánh công bằng baseline vs TIL trên cùng input.
- **Expert review is central.** Professor/supervisor hoặc teaching-experienced reviewer xem Evaluation A/B blind, đánh giá correctness, evidence validity, actionability, usefulness, unsupported inference, missed opportunities.
- **Safe claim:** “stronger alignment with expert pedagogical judgement”, “fewer unsupported claims”, “more evidence-grounded/actionable feedback”.
- **Avoid overclaiming:** không claim AI expert-level, không claim thay thế expert, không claim simulated students là real students, không claim real learning gains.
- **Student behaviour layer:** Có thể dùng Generative Agents concepts như memory stream, retrieval, reflection, planning, state update để tạo literature-informed believable virtual student behaviour, nhưng đây là supporting contribution chứ không phải main proof.

---

## 1. Executive summary

This thesis proposes and prototypes **PixelClass TIL**, a Teacher-in-the-Loop research system that uses simulated classroom teaching sessions as a controlled environment for evaluating AI-generated pedagogical feedback. The central research problem is not merely whether large language models can generate classroom-like dialogue, but whether an evidence-grounded evaluation pipeline can produce pedagogical feedback that is more specific, trustworthy, actionable, and aligned with expert judgement than a generic LLM evaluator.

The MVP combines three parts:

1. **Scenario Blueprint / Scenario Builder** — defines a micro-lesson, learning objectives, lesson phases, expected student behaviours, misconceptions, student-agent mechanisms, and claim guardrails.
2. **Live Mode** — allows a human teacher to teach a 15–30 minute micro-lesson to virtual student personas, generating exploratory classroom transcripts.
3. **Transcript Benchmark Mode** — evaluates fixed transcripts with both a generic baseline evaluator and the proposed Teacher-in-the-Loop evidence-grounded evaluator, verifies evidence links, and presents blinded Evaluation A/B outputs for expert review.

The intended Honours-level contribution is a research-grade evaluation framework and MVP benchmark, not a claim that AI can fully simulate real classrooms or replace expert pedagogical judgement.

---

## 2. Refined thesis positioning

### 2.1 Working title

**PixelClass TIL: A Teacher-in-the-Loop Benchmark System for Evaluating Pedagogical Feedback in Simulated Classroom Teaching Sessions**

Alternative shorter title:

**PixelClass TIL: Evidence-Grounded Evaluation of Pedagogical Feedback in Simulated Classrooms**

### 2.2 Final one-sentence framing

PixelClass TIL is a Teacher-in-the-Loop benchmark system that uses simulated classroom transcripts to compare generic LLM feedback with an evidence-grounded pedagogical evaluator through deterministic evidence verification and blinded expert review.

### 2.3 Old direction vs refined direction

The original direction focused on **agentic AI / multi-agent classroom simulation for testing and optimising teaching methods**. That direction remains relevant, but it is too broad and hard to validate within an Honours thesis because proving realistic classroom simulation or real teaching improvement would require more data, ethics approval, longitudinal evaluation, and expert consensus.

The refined direction focuses on **evaluation quality**:

- The simulated classroom becomes the controlled transcript-generation and demonstration environment.
- The fixed transcript benchmark becomes the main experimental comparison.
- The proposed system is evaluated by how well its feedback is evidence-grounded, actionable, and aligned with expert judgement.

This is not a topic change. It is a defensible contribution shift from “simulation spectacle” to “evaluation framework and benchmark”.

---

## 3. Research gap

Existing LLM-based educational simulations and AI teaching tools can generate classroom-like dialogue, virtual students, lesson interactions, and feedback. However, many systems lack a reliable, theory-grounded, evidence-verifiable mechanism for evaluating the pedagogical quality of teaching across lesson-style classroom transcripts.

The key gap is:

> Existing LLM-based educational simulations can generate realistic or believable classroom-like conversations, but they rarely provide a controlled benchmark pipeline for comparing pedagogical feedback quality, verifying evidence, and measuring alignment with expert teaching judgement.

This gap matters because teacher-facing AI feedback can sound plausible while being vague, unsupported, or disconnected from the actual classroom transcript. For educational AI to be useful in teacher training or reflective practice, feedback must be grounded in observable evidence, linked to pedagogical criteria, and reviewable by humans.

---

## 4. Aim and objectives

### 4.1 Aim

To design, implement, and evaluate a Teacher-in-the-Loop evidence-grounded benchmark system for comparing pedagogical feedback quality across simulated classroom teaching transcripts.

### 4.2 Objectives

1. **Build a controlled classroom transcript testbed** using simulated virtual student personas and lesson scenarios.
2. **Design fixed benchmark transcripts** representing strong and weak teaching patterns, misconceptions, scaffolding issues, participation issues, and missed pedagogical opportunities.
3. **Implement two evaluator conditions:** a generic baseline evaluator and a Teacher-in-the-Loop evidence-grounded evaluator.
4. **Verify feedback evidence** by checking whether claims cite valid transcript turn IDs and quotes.
5. **Support blinded expert review** where a reviewer compares Evaluation A and Evaluation B without seeing which condition produced each output.
6. **Compute expert-review metrics** such as acceptance rate, correction rate, rejection rate, evidence validity rate, unsupported inference rate, and usefulness ratings.
7. **Define safe academic claims and limitations** to avoid overstating simulation realism, expert replacement, or real student learning outcomes.

---

## 5. Research questions

### RQ1 — Evidence-grounded feedback quality

To what extent does the Teacher-in-the-Loop evidence-grounded evaluator produce more specific, transcript-grounded, and actionable pedagogical feedback than a generic LLM evaluator?

### RQ2 — Expert alignment

Does the Teacher-in-the-Loop evaluator show stronger alignment with expert pedagogical judgement than the generic baseline evaluator in blinded A/B review?

### RQ3 — Evidence validity and unsupported inference

Does requiring explicit evidence turn IDs and evidence quotes reduce unsupported claims, fabricated evidence, and vague feedback compared with generic LLM feedback?

### RQ4 — Missed pedagogical opportunities

How effectively does the TIL evaluator identify missed pedagogical opportunities such as unaddressed misconceptions, weak scaffolding, insufficient formative assessment, and low participation?

### RQ5 — Usefulness for teacher reflection

Do expert or teaching-experienced reviewers rate the TIL feedback as more useful and actionable for teacher reflection than baseline feedback?

---

## 6. Expected contributions

### 6.1 Primary contribution

A working Teacher-in-the-Loop benchmark pipeline for evaluating pedagogical feedback on classroom transcripts. This includes:

- fixed benchmark transcripts;
- baseline vs TIL evaluator comparison;
- evidence-linked feedback format;
- deterministic evidence verification;
- blinded A/B expert review;
- expert-review metrics.

### 6.2 Secondary contribution

A literature-informed virtual student behaviour layer that supports believable simulated classroom challenges such as misconceptions, anxiety, disengagement, overconfidence, quiet participation, peer influence, and gradual understanding change.

This layer is informed by Generative Agents-style mechanisms such as:

- memory stream;
- retrieval;
- reflection;
- planning;
- state update.

The correct claim is **literature-informed believable virtual student behaviour**, not real-student-data-informed simulation unless real classroom/student data and ethics approval are obtained.

### 6.3 Practical contribution

A runnable FastAPI + React/Vite MVP that can be demonstrated to supervisors and extended into expert review studies, larger benchmarks, and future PhD-level research.

---

## 7. Literature positioning

The literature review should not be rewritten from scratch. The existing literature around agentic AI, multi-agent classroom simulation, teacher-in-the-loop systems, GPTeach, EducationQ, SimClass, TeachTune, AI-Agent School, and Generative Agents remains relevant. The main required update is to the **Research Gap** and **Proposed Positioning** sections.

### 7.1 How prior work motivates the project

Relevant prior work supports three parts of this thesis:

1. **LLM-based educational simulation and virtual classrooms** — motivates simulated classrooms as a controllable environment for teaching practice and transcript generation.
2. **Teacher-in-the-loop educational AI** — motivates keeping a human teacher/reviewer in control rather than treating AI as an autonomous replacement.
3. **Generative Agents and agentic simulation concepts** — motivate believable virtual student behaviour through memory, retrieval, reflection, planning, and state updates.
4. **Pedagogical feedback and formative assessment theory** — motivates rubric dimensions such as conceptual accuracy, scaffolding, formative assessment, questioning, and missed pedagogical opportunities.

### 7.2 Research gap wording for the literature review

Existing systems demonstrate that LLMs can generate classroom-like interactions, simulate student personas, and provide feedback. However, there remains limited work on controlled, evidence-verifiable benchmarks for evaluating the pedagogical quality of AI feedback across lesson-style transcripts. In particular, prior work often emphasises simulation generation or tutoring behaviour, while providing less support for blinded comparison, evidence verification, expert annotation, and measurement of unsupported pedagogical claims.

### 7.3 Proposed positioning wording

This thesis positions simulated classroom interaction as a **testbed** for pedagogical evaluation rather than as the sole research output. The proposed contribution is a Teacher-in-the-Loop benchmark framework that compares generic and evidence-grounded evaluators on fixed transcripts, verifies evidence links, and uses blinded expert review to assess feedback correctness, usefulness, and alignment with pedagogical judgement.

---

## 8. System overview

### 8.1 Current repository

The active implementation repository is:

`D:/Code/til-classroom-sim`

Remote GitHub repository:

`https://github.com/healerHK/AI-Agent-Teaching-Method-Simulator`

Current pushed MVP branch:

`pixelclass-til-v2-mvp`

Commit:

`007cff5 feat: add PixelClass TIL v2 MVP`

### 8.2 Technology stack

- **Backend:** FastAPI, Pydantic, SQLite, deterministic fallback evaluators, optional external LLM provider integration.
- **Frontend:** React, TypeScript, Vite, pixel-style classroom UI.
- **Data:** Golden benchmark transcript folders and SQLite-backed evaluation/review tables.
- **Verification:** Pytest backend tests, TypeScript/Vite production build, direct API smoke tests, browser smoke tests.

### 8.3 Existing backend modules

Key backend modules include:

- `app/main.py` — FastAPI app and route definitions.
- `app/v2_models.py` — v2 scenario, live mode, benchmark, and review response models.
- `app/v2_service.py` — v2 orchestration service for scenario blueprint, live mode, transcript benchmark mode, and review metrics.
- `app/session_controller.py` — classroom session state and student response flow.
- `app/evaluator_runner.py` — baseline and TIL evaluator execution.
- `app/evidence_verifier.py` — deterministic evidence verification.
- `app/blinding.py` — blinded review mappings and annotations.
- `app/benchmark_loader.py` — golden benchmark transcript loader.

### 8.4 Existing frontend modes

The v2 frontend exposes three main cards:

1. **Scenario Builder / Thesis Blueprint**
2. **Live Mode: Micro-lesson Simulation**
3. **Transcript Benchmark Mode**

---

## 9. MVP design

### 9.1 Mode 1 — Scenario Blueprint / Scenario Builder

The Scenario Blueprint mode presents the research framing and lesson design in one place. It includes:

- thesis positioning;
- research gap;
- main contribution;
- safe claim;
- 15–30 minute micro-lesson scenario;
- lesson phases;
- misconceptions;
- virtual student behaviour claim;
- Generative Agents-inspired mechanisms;
- planned benchmark variants;
- claim guardrails.

This mode is useful for supervisor explanation because it shows that the MVP is not random UI work; it is an operationalised research design.

### 9.2 Mode 2 — Live Mode

Live Mode allows a human teacher to teach virtual students in a 2D pixel classroom. The current v2 scenario is:

`python_loops_full_lesson_001`

Live Mode is designed as a **15–30 minute micro-lesson proxy**. The current compact implementation uses eight teacher turns to represent lesson progression.

Live Mode is used for:

- demo evidence;
- usability/pilot testing;
- exploratory transcript collection;
- showing the teacher-in-the-loop interaction;
- generating candidate transcripts that may later be frozen for benchmark use.

Live Mode should not be the only benchmark because different live sessions produce different transcripts, making evaluator comparison less controlled.

### 9.3 Mode 3 — Transcript Benchmark Mode

Transcript Benchmark Mode is the main research comparison path. It uses a fixed transcript so that both evaluator conditions receive the same input.

Pipeline:

```text
fixed transcript
  -> generic/baseline evaluator
  -> TIL evidence-grounded evaluator
  -> evidence verifier
  -> blinded expert review
  -> metrics summary
```

Current available benchmark transcripts:

- `python_loops_strong_001`
- `python_loops_weak_001`

The weak transcript is useful because it contains clear missed misconceptions and weak scaffolding, allowing the TIL evaluator to demonstrate evidence-linked feedback.

---

## 10. Scenario design: Python loops micro-lesson

### 10.1 Scenario identity

Scenario ID:

`python_loops_full_lesson_001`

Title:

**Python loops micro-lesson: prediction, tracing, misconception response, and closure**

Estimated duration:

**25 minutes**

Subject domain:

**Introductory programming**

Education level:

**Upper-secondary / early undergraduate**

Learning objective:

Students explain that a Python for-loop executes its body once for each item in a sequence and can trace how the loop variable changes across iterations.

### 10.2 Core misconceptions

- One written `print` statement means one execution.
- The loop variable updates before the body runs.
- The list length and output count are unrelated.
- Students can predict output without explaining the iteration mechanism.

### 10.3 Lesson phases

1. **Opening and prior knowledge activation** — 0–4 minutes  
   Teacher goal: activate existing understanding of repetition and prediction.  
   Evidence focus: teacher invites prediction; teacher distributes participation.

2. **Concept explanation and modelling** — 4–10 minutes  
   Teacher goal: explain loop variable update and model one trace.  
   Evidence focus: conceptual accuracy; scaffolding; response to misconception.

3. **Guided practice and misconception event** — 10–18 minutes  
   Teacher goal: ask students to complete a trace table and respond to misconceptions.  
   Evidence focus: formative assessment; missed pedagogical opportunity; student reasoning elicitation.

4. **Formative assessment checkpoint** — 18–24 minutes  
   Teacher goal: check whether students can predict output and explain why each value appears.  
   Evidence focus: checking understanding; quality of follow-up questions.

5. **Reflection and closure** — 24–30 minutes  
   Teacher goal: summarise concept and connect student evidence to next teaching action.  
   Evidence focus: closure; next-step teaching action; remaining misconceptions.

---

## 11. Virtual student behaviour layer

### 11.1 Claim level

The virtual student behaviour layer should be described as:

**literature-informed believable virtual student behaviour**

If a professor or teaching expert calibrates/reviews the behaviour, it can be described as:

**expert-informed simulated student behaviour**

Only if real student/classroom data and ethics approval are obtained should it be described as:

**real-student-data-informed simulation**

### 11.2 Persona types

The current and planned personas include:

- high achiever;
- misconception-heavy student;
- anxious beginner;
- disengaged student;
- curious/distracted student;
- quiet/low-participation student;
- overconfident student;
- peer-influenced student.

### 11.3 Generative Agents-inspired mechanisms

The behaviour layer is inspired by Generative Agents concepts but adapted for pedagogical simulation:

- **Memory stream:** each persona tracks recent classroom events, predictions, confusion, corrections, and confidence changes.
- **Retrieval:** student responses are influenced by recency, relevance to the current teacher prompt, and importance of misconceptions.
- **Reflection:** repeated evidence can become a higher-level belief, such as understanding that `print(number)` runs once per list item.
- **Planning:** personas decide whether to answer, stay silent, ask a question, or reveal confusion based on role and lesson phase.
- **State update:** confidence, misconception strength, participation, and affect update after teacher turns.

This student layer supports the benchmark by creating pedagogically meaningful events, but it is not the main validation target of the thesis.

---

## 12. Evaluation framework

### 12.1 Evaluator conditions

The benchmark compares two conditions:

1. **Baseline evaluator**  
   A generic LLM-style evaluator that gives broad teaching feedback without strict evidence grounding.

2. **TIL evidence-grounded evaluator**  
   A rubric-based evaluator that must produce feedback items with:
   - criterion;
   - claim;
   - score;
   - evidence turn IDs;
   - evidence quotes;
   - suggested action;
   - confidence.

### 12.2 Rubric dimensions

Current rubric dimensions include:

- pedagogical content knowledge / conceptual accuracy;
- scaffolding;
- formative assessment;
- cognitive questioning;
- missed pedagogical opportunity.

### 12.3 Evidence verification

The evidence verifier checks whether the evaluator’s feedback is grounded in the transcript. It can detect:

- missing evidence;
- quote not found;
- turn ID not found;
- speaker mismatch;
- invalid score;
- invalid criterion;
- unsupported claim.

Important limitation: deterministic evidence verification confirms that evidence references exist in the transcript, but it does not by itself prove full pedagogical correctness. That is why expert review is still needed.

---

## 13. Expert review protocol

### 13.1 Reviewer role

The reviewer can be:

- supervisor/professor;
- tutor;
- experienced teacher;
- teaching-experienced academic.

If only one expert is available, the thesis should call this **single-expert review** or **expert-informed pilot evaluation**, not full expert consensus.

### 13.2 Blinding

The reviewer sees:

- Evaluation A;
- Evaluation B.

The reviewer should not see whether A or B is baseline/TIL during annotation.

### 13.3 Rating dimensions

Per feedback item, reviewers can rate or flag:

- pedagogical correctness;
- evidence validity;
- actionability;
- usefulness;
- unsupported inference;
- fabricated evidence;
- pedagogical disagreement;
- missed issue;
- optional comment;
- review time.

### 13.4 Derived metrics

Metrics include:

- **Expert acceptance rate:** accepted feedback items / reviewed feedback items.
- **Correction rate:** items requiring human score change or pedagogical disagreement / reviewed feedback items.
- **Rejection rate:** rejected feedback items / reviewed feedback items.
- **Evidence validity rate:** feedback items without fabricated evidence / reviewed feedback items.
- **Unsupported inference rate:** unsupported inference flags / reviewed feedback items.
- **Usefulness mean:** average usefulness rating from 1 to 5.
- **Missed-opportunity precision/recall/F1:** planned for richer annotated benchmark runs.

---

## 14. Methodology

### 14.1 Research design

The thesis uses a design-and-evaluation methodology:

1. Design a pedagogically grounded benchmark framework.
2. Build a runnable MVP.
3. Use fixed transcripts to compare evaluator conditions.
4. Verify evidence links deterministically.
5. Conduct blinded human/expert review.
6. Analyse acceptance, correction, rejection, evidence validity, unsupported inference, and usefulness metrics.

### 14.2 Data sources

Current data sources:

- hand-designed golden benchmark transcripts;
- simulated/live session transcripts generated by the MVP;
- feedback outputs from baseline and TIL evaluators;
- deterministic evidence verification results;
- expert or reviewer annotations.

Future data sources may include:

- additional subject scenarios;
- real teacher micro-teaching sessions;
- expert-calibrated student behaviour scripts;
- real classroom/student data only if ethics approval is obtained.

### 14.3 Calibration vs validation

If expert feedback is used to refine the framework, calibration and validation should be separated:

```text
literature-derived rubric
  -> expert calibration on calibration transcripts
  -> refined TIL evaluation framework
  -> validation on held-out/new transcripts
```

The same examples should not be used both to refine the rubric and to claim final validation unless the result is clearly labelled as pilot/calibration evidence.

---

## 15. Expected results and safe claims

### 15.1 Expected result pattern

The expected result is that TIL evidence-grounded feedback will:

- cite more valid transcript evidence;
- provide more specific pedagogical claims;
- identify missed misconceptions and scaffolding gaps more clearly;
- require fewer expert corrections;
- be rated more actionable/useful by expert reviewers;
- have fewer unsupported or vague claims than baseline feedback.

### 15.2 Safe claims

The thesis can safely claim, if supported by results:

- The TIL evaluator showed stronger alignment with expert pedagogical judgement than the generic baseline.
- The TIL evaluator produced more evidence-grounded and actionable feedback.
- The evidence-verification layer helped detect unsupported or weakly grounded feedback.
- The benchmark framework supports teacher reflection and expert review.

### 15.3 Claims to avoid

Do not claim:

- The system is expert-level.
- The system replaces teacher educators or expert reviewers.
- The simulated students behave like real students.
- The system proves improvement in real student learning.
- The evaluator accurately evaluates teachers in the wild.
- One expert review equals full validation or expert consensus.

---

## 16. Threats to validity

### 16.1 Internal validity

Threats:

- The same LLM family may be used for simulation and evaluation.
- Prompt wording may influence evaluator output.
- Repeated LLM runs may vary.
- Reviewers may infer which condition is TIL over time.

Mitigations:

- Use fixed transcripts.
- Use the same transcript for both evaluator conditions.
- Store prompt/model/version metadata.
- Blind evaluator labels as Evaluation A/B.
- Report repeated-run stability where possible.

### 16.2 Construct validity

Threats:

- The rubric may not capture all aspects of teacher expertise.
- Evidence verification checks quote existence, not full pedagogical meaning.
- Researcher annotation is not the same as expert validation.

Mitigations:

- Define rubric dimensions before experiments.
- Separate fabricated evidence, unsupported inference, and pedagogical disagreement.
- Use educator reviewers where possible.
- Treat early results as pilot evidence.

### 16.3 External validity

Threats:

- Introductory programming may not generalise to other subjects.
- Synthetic transcripts may not represent real classroom complexity.
- Pixel UI demo sessions may not generalise to real teacher-training environments.

Mitigations:

- State scope clearly.
- Add mathematics/science scenarios if time allows.
- Avoid claims about real learning gains.
- Treat the MVP as a research instrument, not a deployed classroom product.

### 16.4 Conclusion validity

Threats:

- Pilot dataset may be small.
- A small number of reviewers limits reliability.
- Multiple metrics may encourage overinterpretation.
- Failed provider/API runs may bias results if hidden.

Mitigations:

- Report dataset size and failed runs.
- Use repeated runs when possible.
- Focus conclusions on evidence validity and expert alignment, not broad real-world effectiveness.

---

## 17. Current implementation status

As of commit `007cff5`, the MVP includes:

### Backend

- v2 scenario endpoint;
- live session start endpoint;
- live teacher turn endpoint;
- transcript benchmark run endpoint;
- expert review summary endpoint;
- v2 API tests;
- evidence verification;
- baseline/TIL evaluator execution;
- blinded review mapping;
- annotation storage.

### Frontend

- home screen with three v2 modes;
- Scenario Builder / Thesis Blueprint panel;
- Live Mode pixel classroom with current phase and protocol notes;
- Transcript Benchmark Mode panel;
- blinded review UI;
- metrics summary UI.

### Verification results from latest build

Backend v2 tests:

```text
uv run python -m pytest tests/test_v2_mvp_api.py -q
3 passed
```

Full backend tests:

```text
uv run python -m pytest -q
27 passed
```

Frontend build:

```text
npm run build
✓ built
```

API smoke confirmed:

- live session starts;
- live teacher turn returns student turns;
- benchmark runs on `python_loops_weak_001`;
- baseline verifier can return `unsupported`;
- TIL verifier returns `verified`;
- blinded labels are Evaluation A/B.

Browser smoke confirmed:

- home screen rendered;
- Scenario Blueprint rendered;
- Live Mode rendered;
- teacher turn updated transcript rows;
- Benchmark Mode rendered;
- blinded review feedback cards rendered;
- console errors: 0.

---

## 18. How to run the MVP

Backend:

```bash
cd D:/Code/til-classroom-sim/backend
uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd D:/Code/til-classroom-sim/frontend
export PATH='/c/Program Files/nodejs':"$PATH"
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173/
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Key routes:

```text
GET  /api/v2/scenarios
POST /api/v2/live/sessions
POST /api/v2/live/sessions/{session_id}/turn
POST /api/v2/transcript-benchmark/run
GET  /api/v2/expert-review/summary/{reviewer_id}
```

---

## 19. Next development plan

### 19.1 Immediate MVP polish

1. Add scenario selector to choose strong/weak/future variants.
2. Add richer expert annotation form with partial accept, edit level, actionability, usefulness, unsupported inference, and comments.
3. Export expert review annotations to CSV.
4. Add a supervisor-demo testing guide.
5. Update README to reflect v2 direction.
6. Add screenshot capture for the three MVP modes.

### 19.2 Benchmark expansion

Add fixed transcript variants:

- `python_loops_missed_misconception`
- `python_loops_poor_scaffolding`
- `python_loops_low_participation`
- `python_loops_overconfident_student`
- `python_loops_strong_teacher_v2`

Longer-term target:

```text
5 scenarios × 3-5 variants × 2 evaluator conditions × repeated runs
```

### 19.3 Research-writing tasks

1. Rewrite literature review Research Gap section.
2. Rewrite Proposed Positioning section.
3. Add methodology section for fixed transcript benchmark.
4. Add expert review protocol section.
5. Add threats to validity and limitations.
6. Add system architecture diagram and evaluation pipeline diagram.

### 19.4 Supervisor/expert review preparation

Prepare a compact review pack:

- one-page thesis summary;
- one-page rubric guide;
- blinded Evaluation A/B review sheet;
- transcript sample;
- annotation CSV template;
- consent/ethics notes if involving external participants.

---

## 20. Ethics and data boundaries

This MVP currently uses synthetic or designed classroom transcripts and simulated student behaviour. It should not claim real student validity without appropriate data and ethics approval.

If real teachers, supervisors, tutors, or students participate:

- clarify whether the activity is coursework feedback, pilot evaluation, or research data collection;
- seek supervisor guidance on ethics requirements;
- avoid collecting unnecessary personal data;
- anonymise reviewer/teacher/student identifiers;
- store data securely;
- report limitations clearly.

For the current Honours MVP, the safest path is to use:

- synthetic benchmark transcripts;
- single-expert or supervisor review as pilot/expert-informed evidence;
- no claim about real student learning outcomes.

---

## 21. Supervisor pitch

This project is not trying to prove that AI can replace teachers or perfectly simulate real classrooms. Instead, it builds a controlled benchmark system for asking a narrower and more defensible research question: when an AI evaluates a teaching transcript, can a Teacher-in-the-Loop, evidence-grounded evaluator produce feedback that is more specific, verifiable, actionable, and aligned with expert judgement than generic LLM feedback?

The simulated classroom provides the testbed. The fixed transcript benchmark provides the fair comparison. The evidence verifier and blinded expert review provide the evaluation mechanism.

---

## 22. Final thesis memory checkpoint

If this file is being read later to recover project context, remember these points first:

1. The main contribution is **evaluation framework/benchmark**, not full classroom realism.
2. Live Mode is for demo/pilot; Transcript Benchmark Mode is the main comparison.
3. Baseline feedback may be vague or unsupported; this contrast is useful.
4. TIL feedback must cite evidence turn IDs and quotes.
5. Human/expert review should be blinded A/B.
6. Use safe claims around expert alignment and evidence validity.
7. Do not claim expert replacement, real-student fidelity, or real learning gains.
8. Generative Agents supports the student behaviour layer only.
9. The current build is on branch `pixelclass-til-v2-mvp`, commit `007cff5`.
10. Next build should focus on expert annotation/export and README/demo polish.
