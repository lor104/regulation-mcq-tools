---
name: regulation-mcq-impact
description: Compare two editions of a regulation document section by section, build a changelog (changes AND no-changes), then flag which existing multiple-choice exam questions (MCQs, provided as a CSV) are affected and what type of update each needs. Use this whenever the user provides two editions/versions of regulations, codes, standards, or policies plus a question bank, and wants to know what changed, which questions are outdated, or which test items need updating — even if they just say "check my questions against the new edition" or "what changed between 2023 and 2026".
---

# Regulation edition change → MCQ impact review

Inputs (always provided):
1. An **older edition** of the regulations (usually PDF)
2. A **newer edition** of the regulations
3. A **CSV of MCQs** written against the older edition. Expected columns:
   `QuestionID, Question, Answer1, Answer2, Answer3, Answer4, CorrectAnswer, CodeReference`

Goal: report what changed between editions, section by section, and then flag the
questions affected by those changes. **Do not rewrite or edit any question.** The
user's team (and SMEs) make the actual edits. This skill only diagnoses and flags.

## Ground rules

- **Use only the provided files.** Do not bring in outside knowledge about the
  regulation topic. Every claim must trace back to a specific clause in one of the
  two editions.
- **Ask if unclear, don't assume.** If a judgement call could go either way (for
  example, whether a wording-only change affects a question), list it separately
  as "possibly affected — needs your call" and ask the user. Don't decide quietly.
- **Never modify the source files.** If you produce a cleaned or annotated file,
  save it as a new file in `1 Impact/` of the run folder (see "Outcomes folder" below).
- **Double-check counts.** Totals of flagged and unaffected questions must add up
  to the number of questions in the CSV. Count the list itself; don't estimate.

## Step 1 — Extract text from both editions

Run the bundled script for each PDF:

```bash
bash <skill-dir>/scripts/extract_pdf_text.sh "<path to edition.pdf>" > <scratch>/<year>.txt
```

The script tries `pdftotext`, then macOS PDFKit, then `pypdf`. It also normalizes
whitespace and puts each section heading, clause (`1.1`, `4.2` …) and lettered
sub-item (`a)`, `b)` …) on its own line, so the editions can be compared line by line.

The CSV may have line breaks inside cells, which can split words (for example
"Ju\n ne" or "organization\n s"). Read it with a real CSV parser and rejoin
those words before comparing answer text.

## Step 2 — Compare editions section by section

Run `diff` on the two normalized text files to find candidates, then read each
section of both editions yourself to confirm. Diffs are noisy. Ignore changes that
are only whitespace, spacing or typo fixes (for example "ofdisease" → "of disease"),
but note in one line that they exist.

Look for these kinds of change:
- **Values changed** — numbers, timeframes, thresholds, distances, counts
- **Clauses added** — especially "Notwithstanding Section X…" exceptions that
  override an existing rule without changing its wording
- **Clauses removed**, which shifts the numbering of the clauses after them
- **Sections moved or renumbered** — same content under a new section number
- **Scope narrowed or widened** — for example "all honey products" → "honey
  offered for sale or distribution"
- **New alternatives** — "X" → "X or Y"
- **Items removed from or added to lists** of examples or requirements
- **Internal conflicts in the newer edition** — one clause updated while a related
  clause elsewhere was not (for example, training now accepts a state license, but
  the permit application still requires course proof). Flag these; don't resolve them.

### Changelog format

Report **every section in order**, including sections with no changes. For each section:

```
**Section N – Title:** No change.            ← or "Changed."
- N.x: <old> → <new>   (quote the specific values/wording that changed)
- New N.y: <summary>
- Old N.z removed: <summary>; later clauses renumbered (N.z+1 → N.z …)
- Moved: was Section M, now Section N (content unchanged)
```

If two sections swap places, report them together so the move is clear.

## Step 3 — Map each question to the changelog

For **every** question in the CSV:

1. Find the clause in its `CodeReference` in the older edition, and confirm the
   keyed answer matches it. If the reference was already wrong in the older
   edition, mention it, but treat it as a pre-existing issue.
2. Find the same rule in the newer edition. It may have moved, been renumbered,
   changed, gained an exception, or been removed.
3. Check the question against that rule. A question is **affected** if any of these is true:
   - the keyed correct answer is now wrong
   - the correct answer is no longer among the options, or several options are
     now arguably correct
   - the question's wording describes something that changed (a threshold,
     scope, or condition)
   - the rule the question tests was removed
   - the section number in `CodeReference` changed (even if the answer is still right)
   - the question's scope no longer matches the rule's scope (for example, the
     stem asks about "honey labels" but the rule now covers only honey "offered
     for sale or distribution"). Flag these as **Question text**, even when the
     keyed answer is still correct.
   - the question tests the **un-updated side of an internal conflict** (see below)
4. Also check other clauses that might affect the question. Changes in a different
   section can affect it, such as a new exception clause or a related requirement.

### Handling internal conflicts

When the new edition clearly changes one clause but leaves a related clause stale
(for example, 14.1 now says "course **or** state license", while 3.3(e) still
requires course proof in the permit application):
- A question that tests the **clearly changed clause** (14.1) gets a concrete
  update (for example Answer options, Correct answer), because the new wording is explicit.
- Questions that test the **section holding the stale clause** (any question
  referencing 3.3, even an unchanged sub-item like 3.3(d)) go to **SME review**.
  That section's requirements are now in doubt, and an SME must decide how to
  reconcile them. Mention the specific conflict in the comment.

## Step 4 — Assign update type and comment

Allowed update types (use one or more, comma-separated):
- **Question text**
- **Answer options**
- **Correct answer**
- **Code reference**
- **SME review** — use when the right fix is ambiguous: two options are both
  arguably correct, the rule was removed (retire or replace?), or the question
  tests the stale side of an internal conflict. Don't combine SME review with other types. Explain what the
  SME needs to decide.

The update comment should say exactly what needs to change and why, quoting the
new values ("Change the correct answer from '48 hours' to '24 hours'. That option
is already on the list."). Don't write the new question. Only describe the fix.

## Output

Return, in this order, in chat. Also save the same content as
`Impact Report (<YYYY>).md` in `1 Impact/` of the run folder (see "Outcomes folder"
below), where `<YYYY>` is the newer edition's year:

1. **Changelog**: section by section, as above.
2. **Affected questions table**. Use exactly these columns, replacing the
   years with the actual editions:

| Q | Question | Section (2023 → 2026) | What changed | Why it's affected | Update type | Update comment |
|---|---|---|---|---|---|---|

   - `Q` = QuestionID. `Question` = full question text (cleaned of line breaks).
   - `Section` = old reference → new reference (for example "§11.4 → §12.4",
     "§8.3 → removed", "§5.5 → §5.5 + new §5.6").
   - List questions in ID order. Include "possibly affected" ones only if the
     user confirms. Until then, list them in a separate short "Needs your call"
     note under the table.
3. **Unaffected questions**: a list of their IDs for reference, with the total, for example
   "**Not affected (14):** Q1, 2, 8, …". If an unaffected question sits in a
   changed section (for example its sub-clause didn't change), say so in a short note.
4. **Notes**: issues in the regulation itself (internal conflicts), problems that
   already existed in the older edition, and any judgement calls you need the user
   to make. Keep this short.

Before sending, confirm that flagged + unaffected + needs-your-call = total questions.

## Outcomes folder

Every run saves to its own numbered folder, whether this skill runs on its own or as
part of the mcq-update-pipeline skill.

**If you were given a run folder** (the pipeline, or the mcq-updater skill, gives one),
use it. Don't create another run folder and don't copy the inputs again. Read the
inputs from `<run folder>/inputs/`. Don't write `Run Summary.md`; whoever gave you the
run folder writes it.

**When run by the mcq-update-pipeline skill:** don't stop to ask about the
"Needs your call" items during this step. Finish and save the report with them listed
under "Needs your call". The pipeline asks the user at its checkpoint and records the
answers in this report.

**Otherwise, create one:**
1. Base folder: `Outcomes/` in the folder that holds the question bank CSV, unless the
   user names another location.
2. Date folder: today's date as `YYYY-MM-DD`.
3. Run folder: one more than the highest two-digit number already in the date folder
   (`01` if there is none). Never reuse or overwrite an existing run folder.
4. Copy every file the user provided into `<run folder>/inputs/` byte for byte
   (`cp -p`), keeping the file names. Work from these copies. Leave the originals
   where they are, unchanged.
5. Save this skill's outputs in `<run folder>/1 Impact/`.
6. When finished, write `<run folder>/Run Summary.md` (format below).

```
Outcomes/YYYY-MM-DD/NN/
  inputs/          copies of the files the user provided
  1 Impact/        regulation-mcq-impact
  2 Update/        mcq-updater
  3 Verify/        regulation-mcq-verify
  Run Summary.md
```

**Run Summary.md** (short, for a reader who hasn't seen the work):
- What ran (skill name), date and run folder
- Inputs: each file in `inputs/`, and which file each step read
- Results: the headline counts from each step that ran
- Open items: escalations and anything that needs a human decision, or "None"
- Files: relative links to every output file
