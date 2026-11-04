---
name: mcq-updater
description: Updates a multiple-choice question bank (CSV) to a new edition of a regulation, without asking for approval on each question. Applies the house rules for MCQ updates, writes the updated bank as a new file, logs every change, and reports what changed and what needs a human decision. Use when the user gives an older and newer edition of a regulation plus a question bank (and optionally an impact report from the regulation-mcq-impact skill) and wants the questions updated.
---

# MCQ updater

You update a question bank so it complies with a new edition of a regulation. You work
on your own: decide each change using the rules below, apply it, log it, and report at
the end. Do not stop to ask for approval on individual questions. Only questions the
rules cannot settle are left for a human (see "Escalate instead of changing").

## Inputs

1. Older edition of the regulation (usually PDF)
2. Newer edition of the regulation
3. Question bank CSV written against the older edition. Expected columns:
   `QuestionID, Question, Answer1, Answer2, Answer3, Answer4, CorrectAnswer, CodeReference`
4. Optional: an impact report listing the affected questions and the update type for each.

If no impact report is provided, create one first by following the
regulation-mcq-impact skill in this plugin (`<skill-dir>/../regulation-mcq-impact/SKILL.md`;
it also has the PDF text extraction script). Save it in `1 Impact/` of the same run
folder (see "Outcomes folder" below). Treat the report as a starting point, not the final word: re-check every
flagged question against the new edition's text, and if you find an affected question
the report missed, handle it and say so in the report.

## Outputs

Save all three in `2 Update/` of the run folder (see "Outcomes folder" below).
Use the new edition's year in the names (shown here as `<YYYY>`).

1. **Updated bank:** `Updated Bank (<YYYY>).csv`
2. **Change log:** `Change Log (<YYYY>).csv`
3. **Report:** `Update Report (<YYYY>).md`

If a file with that name already exists, add ` v2`, ` v3` … rather than overwriting.

## Ground rules

- **Never edit the original question bank or the regulation files.**
- **Use only the provided files.** Every change must trace to a quoted clause of the
  new edition. No outside knowledge about the subject.
- **Read the new edition's actual text** for every question you touch. Don't rely on
  the impact report's summary of the rule.
- **Read the CSV with a real CSV parser.** Cells may contain commas, curly quotes or
  line breaks. A line break can split a word ("Octo\n ber") or sit between two words,
  and the correct answer and its matching option may break in different places. When
  comparing answer text, rejoin split words and treat other breaks as spaces. In rows
  you change, write every cell on one line. Leave untouched rows exactly as they are,
  line breaks included.

## Process

1. Copy the original bank byte for byte to the updated-bank file. Edit only the rows
   that change, so untouched rows stay identical to the original.
2. For each flagged question, in ID order:
   a. Quote the new rule and identify what is wrong with the current question.
   b. Consider the possible fixes and choose one using the rules below. If two fixes
      both fit, prefer the one the rules favor; note the alternative in the log.
   c. Run the compliance check (below). If it fails, revise and check again. If it
      still fails after two revisions, escalate.
   d. Write the change to the updated bank and add a row to the change log.
3. Run the file validation (below).
4. Write the report.

## Rules for deciding changes

### How much to change
1. **Make the smallest change that fixes the problem.** If only the section number
   moved and the answer is still right, change only the reference. Don't reword the
   question.
2. **If you are already changing the correct answer, also fix wording that could leave
   two defensible answers.** Example: if the rule sets a minimum ("at least 24 hours"),
   the question should ask for the minimum, or a larger value could be argued correct.
3. **If the question is broader than the new rule, narrow it to match the rule's
   scope**, even when the answer is still right. Example: a requirement that now
   applies only to products offered for sale.
4. **Fix reference errors you notice along the way**, even ones that were already
   wrong in the old edition. Log them as pre-existing.

### Which kind of change to test
5. **When a number or threshold changes, test the change itself.** Use a concrete
   value clearly inside the changed range, away from exact boundary values. Use the
   old edition's value as a wrong answer to catch out-of-date knowledge.
6. **When a new exception is added, test the exception.** Put the condition in the
   question ("With written approval from…") so only one answer can be defended. Where
   it makes sense, have wrong answers on both sides of the correct one (for example
   above and below a number).
7. **When the rule now allows more than one route** (for example "a course or a
   license"), the correct answer must name every route, using the rule's own wording.
8. **When a rule is removed, replace the question rather than retire it.** Write the
   replacement on the clause that now holds that section number, or on a current rule
   on the same topic in the same section. Keep the same QuestionID. Don't duplicate a
   rule another question in the bank already tests.

### Conflicts in the regulation
9. **Don't change a question just because its section contains a conflict.** If the
   clause it tests is unchanged and still correct, leave the question as it is, log it
   as "Unchanged – reviewed", and list the conflict in the report.
10. **Report conflicts inside the new edition** (a clause updated in one place but not
    in another that depends on it) in the report's "Regulation issues" section.
11. **Don't write questions or options that depend on an unresolved conflict.**

### Writing options
12. **Keep all options close in length and grammatical shape.** The correct answer
    must not stand out by being longer or more detailed. If it has to be long,
    lengthen the wrong answers to match (for example, write every option as "X or Y").
13. **Check every wrong answer against the whole regulation, not just the cited
    section.** A wrong answer must not be defensible under any other clause. Watch for
    broad wording such as "including but not limited to".
14. **Remove outdated correct answers entirely.** Keep one as a wrong answer only if
    it is clearly wrong under the new rules.
15. **Prefer wrong answers the regulation permits, requires or encourages** (clearly
    not violations), or ones that test who an obligation applies to (for example the
    regulator rather than a neighbor). Don't invent requirements that sound real
    enough to be argued correct.
16. **Every question has exactly one correct answer.** All other options must be
    incorrect under the new edition. When the rule lists several qualifying items
    (for example, several examples of a violation), use only one of them as an option
    and make it the correct answer. Choose the item that is clearly correct on its own,
    without relying on a qualifier a test-taker could miss.
17. **Keep numeric options in ascending order.**

## Compliance check (every changed question)

Answer each of these from the new edition's text. All must pass.

- **Exactly one option is correct.** The keyed answer is correct under the new edition,
  and every other option is incorrect. If more than one option is correct, or none is,
  the question fails.
- The correct answer matches the quoted clause, and the cited `CodeReference` is the
  clause that says it.
- Read the question cold, as a test-taker who knows the new edition, and confirm you
  would pick only the keyed answer.
- For each wrong answer, try to argue it is correct using any clause in the new
  edition. If you can, it fails.
- The question doesn't depend on an unresolved conflict.
- If options were rewritten: the longest option is no more than 1.5× the length of the
  shortest (numeric options exempt), and the correct answer isn't the only one with a
  different shape.

## Escalate instead of changing

Leave the row unchanged in the updated bank, log it as "Escalated", and put it in the
report's "Needs a human decision" section with your best draft and the reason, when:

- the correct answer depends on an unresolved conflict in the regulation;
- a rule was removed and the section has no current rule on a related topic you could
  test without duplicating another question;
- no version of the question passes the compliance check after two revisions;
- the new edition's text is unclear or appears garbled at the clause you need.

## File validation

Run this after all changes (adjust the file names):

```bash
python3 -I - "<original.csv>" "<updated.csv>" <<'EOF'
import csv, re, sys
o = list(csv.reader(open(sys.argv[1], encoding="utf-8-sig", newline="")))
n = list(csv.reader(open(sys.argv[2], encoding="utf-8-sig", newline="")))
assert len(o) == len(n), f"row count changed: {len(o)} -> {len(n)}"
assert o[0] == n[0], "header changed"
flat = lambda s: re.sub(r"\s+", "", s)  # line breaks in the original may fall anywhere
changed = []
for i, r in enumerate(n[1:], start=1):
    assert len(r) == 8, f"Q{r[0]}: wrong column count"
    if r != o[i]:
        changed.append(r[0])
        assert not any("\n" in c or "\r" in c for c in r), f"Q{r[0]}: changed row has a line break"
        assert r[6] in r[2:6], f"Q{r[0]}: correct answer not an exact option"
    assert sum(flat(x) == flat(r[6]) for x in r[2:6]) == 1, f"Q{r[0]}: correct answer matches no option, or more than one"
    assert len({flat(x) for x in r[2:6]}) == 4, f"Q{r[0]}: duplicate options"
print("OK. Changed rows:", ", ".join(changed) or "none")
EOF
```

Changed rows must match their correct answer exactly. Untouched rows are checked
ignoring spaces and line breaks, because the original bank may break the correct
answer and its matching option in different places; they are never edited to make the
check pass. Confirm the changed rows match exactly the questions logged as "Updated".
Fix and re-run if anything fails. Report the result.

## Change log format (CSV)

One row for **every flagged question**, including unchanged and escalated ones:

`QuestionID, Status, UpdateType, OldQuestion, NewQuestion, OldOptions, NewOptions, OldCorrectAnswer, NewCorrectAnswer, OldReference, NewReference, NewRuleQuote, RulesApplied, Rationale, AlternativeConsidered, ComplianceCheck`

- `Status`: Updated, Unchanged – reviewed, or Escalated
- `UpdateType`: Question text, Answer options, Correct answer, Code reference (one or more)
- `OldOptions` / `NewOptions`: the four options joined with ` | `
- `NewRuleQuote`: the exact new-edition wording the change relies on
- `RulesApplied`: rule numbers from this file, for example `1, 4`
- `ComplianceCheck`: Pass, or what failed and why the question was escalated

## Report format (Markdown)

Write for a reader who hasn't seen the work. Lead with the outcome.

1. **Summary**: one or two sentences, then counts: updated, unchanged after review,
   escalated, and total flagged. Check that they add up.
2. **Changes made**: a table with `Q | What changed | New correct answer | Reference |
   Why (rule)`, in ID order.
3. **Needs a human decision**: each escalated question with the reason and your draft
   fix. Write "None" if empty.
4. **Regulation issues**: conflicts or unclear text in the new edition, and
   pre-existing errors found in the old bank.
5. **Validation**: the file validation output, and confirmation that the original
   files were not modified.
6. **Files**: paths to the updated bank, change log and report.

When you finish, reply with the report's summary, the escalations (if any), and the
three file paths.

## Outcomes folder

Every run saves to its own numbered folder, whether this skill runs on its own or as
part of the mcq-update-pipeline skill.

**If you were given a run folder** (the pipeline always gives one), use it. Don't
create another run folder and don't copy the inputs again. Read the inputs from
`<run folder>/inputs/` and the impact report from `<run folder>/1 Impact/`. Don't
write `Run Summary.md`; the pipeline writes it.

**Otherwise, create one:**
1. Base folder: `Outcomes/` in the folder that holds the question bank CSV, unless the
   user names another location.
2. Date folder: today's date as `YYYY-MM-DD`.
3. Run folder: one more than the highest two-digit number already in the date folder
   (`01` if there is none). Never reuse or overwrite an existing run folder.
4. Copy every file the user provided into `<run folder>/inputs/` byte for byte
   (`cp -p`), keeping the file names. Work from these copies. Leave the originals
   where they are, unchanged.
5. Save this skill's outputs in `<run folder>/2 Update/`.
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
