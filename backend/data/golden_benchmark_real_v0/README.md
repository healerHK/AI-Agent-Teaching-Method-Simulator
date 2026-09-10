# Real Classroom Benchmark v0.4 — Pilot Transcript Layer

This folder is a pilot real-classroom benchmark layer for PixelClass TIL with human-validated final labels and evidence/domain-check flags.

## Included pilot transcripts

1. `real_ela_all_summer_venus_close_read_001_observed`
   - Subject: English Language Arts
   - Focus: All Summer in a Day discussion, Venus informational text, annotation, text-dependent questions
   - Turns: 61
   - Annotation status: human-validated with evidence/domain-check flags

2. `real_ela_archetypal_fool_character_001_observed`
   - Subject: English Language Arts
   - Focus: archetypal theory, the fool, comic relief, irony, literature/pop-culture examples
   - Turns: 590
   - Annotation status: human-validated with evidence/domain-check flags

3. `real_ela_empathy_novel_study_001_observed`
   - Subject: English Language Arts
   - Focus: empathy, social commentary, author techniques, novel-study routines
   - Turns: 78
   - Annotation status: human-validated with evidence/domain-check flags

4. `real_ela_nonfiction_theme_uncertainty_001_observed`
   - Subject: English Language Arts
   - Focus: nonfiction close reading, context, audience inference, themes, uncertainty, textual evidence, rhetorical strategies
   - Turns: 491
   - Annotation status: human-validated with evidence/domain-check flags

5. `real_hs_algebra_tiles_simplifying_001_observed`
   - Subject: Mathematics
   - Focus: algebra tiles and simplifying expressions
   - Turns: 142
   - Annotation status: human-validated with evidence/domain-check flags

6. `real_y7_industrial_tech_timber_assembly_001_observed`
   - Subject: Industrial Technology and Design
   - Focus: timber assembly, sanding, grit selection, workshop routines, guided/independent practice
   - Turns: 124
   - Annotation status: human-validated with evidence/domain-check flags

## Why this exists

Supervisor feedback identified that the synthetic benchmark was technically useful but not realistic enough. These real transcripts improve ecological validity because they include natural disfluencies, uneven participation, classroom routines, implicit materials/tools, and genuine student confusion.

## Claim boundary

Use this as a method/proposal artifact and pilot ecological-validity benchmark layer. Do not claim final model superiority, classroom effectiveness, or absolute human ground truth from six transcripts. The defensible wording is: human-validated annotation set with evidence and domain-check flags. Next steps are to add source-link provenance, collect more transcripts if needed, and obtain independent multi-expert adjudication if the thesis needs stronger ground-truth claims.

## Loader note

The current benchmark loader only accepts `strong` and `weak` variants, so observed real transcripts are stored under `strong/` as a compatibility label. Interpret these as `observed_real_classroom`, not as synthetic strong teaching variants.

## Provenance note

For public YouTube-derived MP3s, keep the YouTube URL/title/channel/access date in thesis metadata when available. Do not include source links in evaluator-visible transcript text unless needed for provenance review.
