# regulation-mcq-tools

A Claude Code plugin for keeping a multiple-choice question (MCQ) bank in line with a
regulation, code, standard or policy document.

## Skills

| Skill | What it does | You provide |
|---|---|---|
| `regulation-mcq-impact` | Compares two editions section by section, and flags which questions are affected and what kind of update each needs. Doesn't edit questions. | Older edition, newer edition, question bank |
| `mcq-updater` | Updates the question bank to the newer edition using fixed house rules, logs every change, and escalates what the rules can't settle. | Older edition, newer edition, question bank (optionally an impact report) |
| `regulation-mcq-verify` | Checks every question against one edition: question text, options, keyed answer and code reference. | One edition, question bank |
| `mcq-update-pipeline` | Runs impact → update → verify in order. It pauses once if the impact step has questions only you can decide. | Older edition, newer edition, question bank |

Claude picks the right skill from your request, or you can run one directly, for
example `/regulation-mcq-tools:mcq-update-pipeline`.

## Question bank format

A CSV with these columns:

`QuestionID, Question, Answer1, Answer2, Answer3, Answer4, CorrectAnswer, CodeReference`

Regulations are usually PDFs. `regulation-mcq-verify` also accepts .txt, .md and .docx.

## Where results go

Every run, whether it's the full pipeline or a single skill, gets its own numbered
folder next to the question bank. Copies of the input files are saved with it:

```
Outcomes/
  2026-11-04/
    01/
      inputs/          copies of the files you provided
      1 Impact/        Impact Report (<year>).md
      2 Update/        Updated Bank, Change Log, Update Report
      3 Verify/        Verification Log (<year>).md
      Run Summary.md
```

A single-skill run has only that skill's subfolder. Your original files are never
changed.

## Install

```
/plugin marketplace add <github-user>/regulation-mcq-tools
/plugin install regulation-mcq-tools@regulation-mcq-tools
```

To try it locally without installing:

```
claude --plugin-dir ./regulation-mcq-tools
```

## Requirements

- `python3` (used for reading CSVs and running checks)
- One of the following for PDF text: `pdftotext` (poppler), macOS (built-in PDFKit),
  or the Python `pypdf` package

## License

MIT. See [LICENSE](LICENSE).
