---
name: regulation-mcq-verify
description: Verify a bank of multiple-choice exam questions (MCQs, provided as a CSV) against ONE edition of a regulation, code, standard or policy document, checking each question's text, answer options, keyed correct answer and code reference, and producing a summary plus a per-question log. Use this whenever the user gives a single regulations file plus a question bank and asks whether the questions are correct, accurate, valid, or consistent with the regulations — even if they just say "check these questions against the regs", "QA this question bank", or "are these MCQs right?". For comparing two editions of a regulation, use regulation-mcq-impact instead.
---

# Verify MCQs against a regulation

Inputs (always provided by the user, different each time. Never reuse files or
findings from earlier runs):
1. A **regulations document** (usually PDF; may also be .txt, .md or .docx)
2. A **CSV of MCQs**. Expected columns:
   `QuestionID, Question, Answer1, Answer2, Answer3, Answer4, CorrectAnswer, CodeReference`
   If the columns differ, map them to these roles and say how you mapped them.
   If you can't tell which column is which, ask.

Goal: decide, for every question, whether it is correct under the provided
regulations, and report what (if anything) is wrong. **Do not edit the source
CSV.** Describe the fixes; don't write new questions unless the user asks.

**Flag only questions that are incorrect.** A question is incorrect only when
something in it is wrong under the regulations: the keyed answer, a distractor
that is also right, a question that misstates the rule, or a wrong code
reference. Do not suggest wording improvements, style changes, clarifications or
rewrites for questions that are correct. A correct question gets status
**Correct** and no notes, even if it could be phrased more precisely.

## Ground rules

- **Use only the provided files.** No outside knowledge about the topic, not even
  to fill gaps. Every finding must trace to a specific clause. If the regulations
  don't cover something a question asserts, say "not supported by the regulations".
  Don't treat it as true.
- **Ask if unclear, don't assume.** When something could go either way, put it
  under "Needs your call" instead of deciding quietly.
- **Never modify the input files.** Save outputs as new files in the run folder (see
  "Outcomes folder" below).
- **Every question gets a log entry**, including the correct ones.
- **Double-check counts.** The status counts must add up to the number of questions.

## Step 1: Extract the regulation text

For a PDF:

```bash
bash <skill-dir>/scripts/extract_pdf_text.sh "<regulations.pdf>" > <scratch>/regs.txt
```

The script tries `pdftotext`, then macOS PDFKit, then `pypdf`. It also puts each
section heading, clause (`1.1`) and lettered sub-item (`a)`) on its own line. For
other formats, extract the text another way and save it to `<scratch>/regs.txt`.

Read the **whole** text yourself. Note extraction glitches (for example words run
together, like "tohouse"). They are not regulation errors, but you can mention them
in one line.

## Step 2: Load the CSV and run structural checks

```bash
python3 -I <skill-dir>/scripts/load_mcqs.py "<questions.csv>" <scratch>/regs.txt > <scratch>/mcqs.json
```

The script reads the CSV with a real CSV parser. **Cells may contain line breaks
that split words** (for example "Ju\n ne" or "organization\n s"). The script rejoins
them when the combined word appears in the regulation text, and otherwise uses a
space. It lists every repair under `repairs`. Review each repair and correct any
that look wrong before comparing answer text. Use the repaired text from here on.

It also flags under `issues`:
- missing columns or empty cells, and duplicate QuestionIDs
- duplicate answer options
- a CorrectAnswer that matches no option, matches only after ignoring
  case, curly quotes or spacing, or matches more than one option
- a CodeReference clause or sub-item that doesn't exist in the regulation text
  (the script only checks numbers like `4.1` and `4.1(c)`. Check other reference
  styles by hand)

These are hints. Confirm each one yourself.

## Step 3: Check every question against the regulations

For each question, read the cited clause **and** any related clauses (definitions,
exceptions such as "Notwithstanding Section X…", lists elsewhere in the document).
Check these four things:

1. **Correct answer**: Does the cited text support the keyed answer? Is it exactly
   one of the four options? Watch for values (numbers, timeframes, distances,
   counts), "and" vs "or", lists that are missing items or include extra ones, and
   exceptions that change the answer.
2. **Answer options**: Exactly one option should be correct. Flag a distractor
   only if the regulations state it as the answer, or it is the same as the keyed
   answer. Read questions the way a test-taker would: if the regulation sets a
   minimum or maximum (for example "at least every 30 days"), the stated value is
   the answer, and a stricter distractor (for example "weekly") is not a second
   correct answer. Flag options that duplicate each other.
3. **Question text**: Flag only if the question states something false under the
   regulations or asks about something the regulations don't cover (for example it
   says "maximum" where the rule is a minimum, or names the wrong subject). Leaving
   out a word like "minimum", "maximum" or a trigger such as "after notification"
   is not an error when the keyed answer is still the only option that matches the
   rule. Don't flag awkward phrasing, style, or minor grammar that doesn't change
   the meaning.
4. **Code reference**: Does it point to the clause that actually supports the
   answer, including the sub-item letter? Is a more specific or more accurate clause
   a better fit? If the answer relies on an exception, the reference should point to
   the exception.

### Status per question

- **Correct**: nothing is wrong. Notes stay empty ("–"). No suggestions.
- **Needs fix**: one or more definite errors. List each with its type and the
  smallest change that makes it correct. Don't rewrite the rest of the question.
- **Needs SME review**: the regulations are ambiguous or contradict themselves, so
  you can't tell whether the question is correct. Say what the SME must decide.

There is no "wording suggestion" status. If a question is correct, it is Correct.

Issue types (use one or more): **Question text**, **Answer options**,
**Correct answer**, **Code reference**.

## Output

Save the log as `Verification Log (<YYYY>).md` in `3 Verify/` of the run folder
(see "Outcomes folder" below), where `<YYYY>` is the regulation edition's year
(don't overwrite an existing file; add a date or number). In chat, give:

1. **Summary**: in the first line, say whether the bank is clean. Then give
   counts by status, then the main issues in plain language, then
   structural or data notes (line-break repairs, file naming, extraction glitches).
2. **Per-question log**: one row per question, in ID order:

| ID | Keyed answer | Ref | Regulation text (short paraphrase) | Status | Issue type | Notes / fix |
|---|---|---|---|---|---|---|

   The saved file also includes a short version of each question's text. For each
   problem, Notes says exactly what to change and why, quoting the regulation
   ("Change correct answer from '48 hours' to '24 hours' per 10.1. That option
   is already listed."). For Correct questions, Notes is "–".
3. **Needs your call**: only real doubts about whether a question is correct, kept
   short. Leave out optional improvements. If there are none, say "None".

Before sending, confirm: number of log rows = number of questions in the CSV, and
the status counts add up to the total.

## Outcomes folder

Every run saves to its own numbered folder, whether this skill runs on its own or as
part of the mcq-update-pipeline skill.

**If you were given a run folder** (the pipeline always gives one), use it. Don't
create another run folder and don't copy the inputs again. Don't write
`Run Summary.md`; the pipeline writes it.

**When run by the mcq-update-pipeline skill:** the question bank is the updated bank
in `<run folder>/2 Update/`, and the regulation is the newer edition in
`<run folder>/inputs/`. Treat them as the user-provided inputs.

**Otherwise, create one:**
1. Base folder: `Outcomes/` in the folder that holds the question bank CSV, unless the
   user names another location.
2. Date folder: today's date as `YYYY-MM-DD`.
3. Run folder: one more than the highest two-digit number already in the date folder
   (`01` if there is none). Never reuse or overwrite an existing run folder.
4. Copy every file the user provided into `<run folder>/inputs/` byte for byte
   (`cp -p`), keeping the file names. Work from these copies. Leave the originals
   where they are, unchanged.
5. Save this skill's outputs in `<run folder>/3 Verify/`.
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
