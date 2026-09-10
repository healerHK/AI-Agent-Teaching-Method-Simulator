# Real-Classroom Benchmark Upgrade Note

## Purpose

The synthetic transcript benchmark remains useful for controlled technical testing, but supervisor feedback identified a realism limitation: synthetic lessons may not capture natural classroom interaction and may contain hallucinated or over-polished dialogue. The next benchmark layer therefore adds anonymised real classroom transcripts as ecological-validity evidence.

## Current pilot real-classroom dataset

- Dataset root: `backend/data/golden_benchmark_real_v0`
- Dataset version: `real_classroom_benchmark_v0.4_six_pilot_transcripts`
- Pilot transcripts: 6
- Annotation status: researcher draft, not expert-reviewed

Included topics:

1. High-school algebra tiles and simplifying expressions.
2. Year 7 industrial technology/timber assembly and sanding techniques.
3. English language arts empathy, social commentary, and novel-study launch.
4. English language arts All Summer in a Day, Venus informational text, close reading, and text-dependent questions.
5. English language arts archetypal theory: the fool, comic relief, irony, and examples from literature/pop culture.
6. English language arts nonfiction close reading: context, audience, theme, uncertainty, evidence, and rhetorical strategy analysis.

## Benchmark design

The real-classroom benchmark should sit beside the synthetic benchmark, not replace it immediately.

1. **Synthetic benchmark:** controlled strong/weak variants for reproducible baseline testing.
2. **Real-classroom benchmark:** observed transcripts for realism, disfluency, uneven participation, implicit materials, and authentic student confusion.
3. **Expert review layer:** human/expert validation of rubric scores, missed opportunities, and evidence spans.
4. **Model evaluation:** run baseline and TIL evaluators on the same fixed real transcripts, with multiple repetitions per model/condition.

## Proposed method framing

PixelClass TIL can be presented as an evidence-grounded evaluation method for classroom transcripts. The core method is not to claim that synthetic simulation proves real learning gains. Instead, the method compares how a generic evaluator and a teacher-in-the-loop/evidence-grounded evaluator identify pedagogical feedback from fixed transcripts.

The benchmark uses transcript provenance, rubric-based expected scores, evidence-span annotations, missed-opportunity annotations, deterministic evidence verification, repeated LLM evaluation runs, and claim boundaries separating technical pipeline success from real classroom effectiveness.

## Draft annotation caveats

These pilot items are not final gold standards. Known limitations: audio transcripts may contain diarisation/transcription errors; two newest MP3-derived transcripts are non-diarised Whisper outputs with heuristic speaker-role labels; video/gesture context is missing or partial; scores are researcher draft labels; six real transcripts are stronger than two/four for method demonstration but still not enough for strong statistical claims.

## Recommended next step

Add YouTube source URL/title/channel/access-date metadata for each public transcript. Run a cheap fallback smoke benchmark after every ingestion. When the user is ready to spend provider quota, rerun the real dataset provider-by-provider with 3–5 repetitions and report variance. For thesis writing, frame this as synthetic controlled benchmark + real-classroom pilot benchmark + expert-review future work. Do not spend time downloading SimClass/GPTeach/TeachTune implementations unless a supervisor specifically asks for executable system baselines.
