---
name: mcq-update-pipeline
description: Run the whole update of a multiple-choice question bank (CSV) to a new edition of a regulation, code, standard or policy, in order — regulation-mcq-impact (what changed and which questions are affected), then mcq-updater (update the questions), then regulation-mcq-verify (check the updated bank against the new edition) — and save every step's output in one numbered run folder. Use when the user gives an older and a newer edition of a regulation plus a question bank and wants the job done end to end, even if they just say "update my questions to the 2026 edition" or "run the full MCQ pipeline". For a single step, use that skill on its own.
---

# MCQ update pipeline

Runs three skills from this plugin in order and saves everything in one run folder:

1. **regulation-mcq-impact**: what changed between editions, and which questions are affected
2. **mcq-updater**: updates the affected questions
3. **regulation-mcq-verify**: checks the updated bank against the newer edition

The three skills sit next to this one. `<skill-dir>` is this skill's base directory, so
their instructions are at:
- `<skill-dir>/../regulation-mcq-impact/SKILL.md`
- `<skill-dir>/../mcq-updater/SKILL.md`
- `<skill-dir>/../regulation-mcq-verify/SKILL.md`

Read each skill's SKILL.md in full before running its step. Each skill's own rules
apply in full. This file only adds the order, the hand-offs and the checkpoint.

## Ground rules

- **Never modify the user's files.** Work only from the copies in `inputs/`.
- **Run the steps in order.** If a step fails or its outputs are missing, stop and tell
  the user what happened. Don't skip ahead.
- **Don't edit a step's outputs**, except adding the checkpoint answers to the impact
  report (Step 1).

## Step 0: Inputs and run folder

The user provides three files:
1. the **older edition** of the regulation
2. the **newer edition**
3. the **question bank CSV**, written against the older edition

Work out which edition is older and which is newer from the titles, years or dates. If
you can't tell, or a file is missing, ask before going on.

Create the run folder:
1. Base folder: `Outcomes/` in the folder that holds the question bank CSV, unless the
   user names another location.
2. Date folder: today's date as `YYYY-MM-DD`.
3. Run folder: one more than the highest two-digit number already in the date folder
   (`01` if there is none). Never reuse or overwrite an existing run folder.
4. Copy the three files into `<run folder>/inputs/` byte for byte (`cp -p`), keeping
   the file names. Confirm each copy with `cmp`.

```
Outcomes/YYYY-MM-DD/NN/
  inputs/          copies of the files the user provided
  1 Impact/        regulation-mcq-impact
  2 Update/        mcq-updater
  3 Verify/        regulation-mcq-verify
  Run Summary.md
```

Tell the user in one line which file is the older edition, which is the newer one, and
where the run folder is.

## Step 1: Impact (in this conversation)

Follow the regulation-mcq-impact skill, using the run folder and the files in `inputs/`.
It saves `Impact Report (<YYYY>).md` in `1 Impact/`.

**Checkpoint.** If the report lists any "Needs your call" items, show them all to the
user at once, each with the question ID and the decision needed, and wait for their
answers. Then add a section to the end of the impact report:

```
## Checkpoint decisions
- Q<ID>: <the decision needed> → <the user's answer, in their words>
```

Questions the user confirms as affected count as flagged for Step 2. If there are no
"Needs your call" items, write "None" in that section and go on without asking.

## Step 2: Update (fresh helper agent)

Start a new general-purpose agent with the Agent tool. Give it absolute paths and tell
it to:
- read and follow `<skill-dir>/../mcq-updater/SKILL.md` in full
- use the run folder `<run folder>` (it already exists, and the inputs are already
  copied)
- use the older edition, newer edition and question bank in `<run folder>/inputs/`
- use the impact report in `<run folder>/1 Impact/` as the impact report, including its
  "Checkpoint decisions" section
- not ask for approval on any question, and reply with the update report's summary, the
  escalations and the three file paths

When it finishes, check that all three files are in `2 Update/` and that the update
report's validation passed. If not, stop and tell the user.

## Step 3: Verify (fresh helper agent)

Start another new general-purpose agent. Give it absolute paths and tell it to:
- read and follow `<skill-dir>/../regulation-mcq-verify/SKILL.md` in full
- use the run folder `<run folder>` (it already exists)
- check `<run folder>/2 Update/Updated Bank (<YYYY>).csv` against the **newer edition**
  in `<run folder>/inputs/`
- not open anything in `1 Impact/` or `2 Update/` other than the updated bank, so the
  check is independent
- reply with the summary and the "Needs your call" items

Questions the verify step flags are reported to the user. Don't send them back to the
updater.

If the Agent tool isn't available, run Steps 2 and 3 in this conversation instead, and
note in the Run Summary that the verify step wasn't run by a separate agent.

## Step 4: Run Summary

Write `<run folder>/Run Summary.md` for a reader who hasn't seen the work. Lead with
the outcome.

1. **Outcome**: one or two sentences, e.g. "12 questions updated, 2 escalated; verify
   found 1 question that still needs a fix."
2. **Inputs**: each file in `inputs/` (older edition, newer edition, question bank),
   and which file each step read
3. **Step 1, Impact**: counts of flagged, unaffected and needs-your-call questions,
   plus the checkpoint decisions
4. **Step 2, Update**: counts of updated, unchanged after review and escalated
   questions, and the IDs of changed rows
5. **Step 3, Verify**: counts by status, and each question that isn't Correct, with its
   issue
6. **Needs a human decision**: escalations from Step 2, plus verify's "Needs fix",
   "Needs SME review" and "Needs your call" items, or "None"
7. **Originals unchanged**: confirm with `cmp` that the user's original files still
   match the copies in `inputs/`
8. **Files**: relative links to every output file

## Reply

In chat, give the outcome first. Then the counts from each step, what needs a human
decision, and links to the run folder and `Run Summary.md`.
