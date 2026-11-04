#!/usr/bin/env python3
"""Load an MCQ CSV, repair line breaks inside cells, and run structural checks.

Usage:
  python3 -I load_mcqs.py <questions.csv> [<regulations.txt>] > <scratch>/mcqs.json

- Reads the CSV with a real CSV parser (cells may contain line breaks).
- Repairs line breaks inside cells. If the text on both sides of a break forms a
  word found in the regulation text (for example "Ju\n ne" -> "June"), the break
  is removed. Otherwise it becomes a space. Every repair is listed so it can be
  double-checked.
- Runs structural checks that do not need judgement: missing columns or cells,
  duplicate IDs, duplicate options, a CorrectAnswer that matches no option (or
  matches only after ignoring case, quotes or spacing), and CodeReferences whose
  clause number does not appear in the regulation text.

Output is JSON: {"columns", "questions": [...], "repairs": [...], "issues": [...]}.
"""
import csv
import json
import re
import sys

EXPECTED = ["QuestionID", "Question", "Answer1", "Answer2", "Answer3", "Answer4",
            "CorrectAnswer", "CodeReference"]
BREAK = re.compile(r"(\S*?)([ \t]*\r?\n[ \t]*)+(\S*)")


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s).strip().casefold()


def main():
    csv_path = sys.argv[1]
    regs = ""
    if len(sys.argv) > 2:
        with open(sys.argv[2], encoding="utf-8") as f:
            regs = f.read()
    vocab = {w.casefold() for w in re.findall(r"[A-Za-z][A-Za-z'’-]*", regs)}

    repairs, issues = [], []

    def fix(qid, col, text):
        def repl(m):
            left, right = m.group(1), m.group(3)
            lw = re.sub(r"^\W+", "", left)
            rw = re.sub(r"\W+$", "", right)
            joined = (lw + rw).casefold()
            if lw and rw and lw[-1].isalpha() and rw[0].isalpha() and joined in vocab:
                out, how = left + right, "joined (word found in regulations)"
            elif not vocab:
                out, how = left + " " + right, "replaced with space (no regulation text given; verify)"
            else:
                out, how = left + " " + right, "replaced with space"
            repairs.append({"QuestionID": qid, "column": col,
                            "before": m.group(0), "after": out, "how": how})
            return out
        return BREAK.sub(repl, text) if ("\n" in text or "\r" in text) else text

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = [c.strip() for c in (reader.fieldnames or [])]
        rows = list(reader)

    missing = [c for c in EXPECTED if c not in cols]
    if missing:
        issues.append({"QuestionID": None, "issue": "missing columns", "detail": missing})

    questions, seen = [], {}
    for i, raw in enumerate(rows, start=2):
        r = {(k or "").strip(): (v or "") for k, v in raw.items()}
        qid = r.get("QuestionID", "").strip() or f"row{i}"
        q = {"row": i}
        for c in cols:
            q[c] = fix(qid, c, r.get(c, "")).strip()
        questions.append(q)

        if qid in seen:
            issues.append({"QuestionID": qid, "issue": "duplicate QuestionID", "detail": f"rows {seen[qid]} and {i}"})
        seen[qid] = i
        for c in EXPECTED:
            if c in cols and not q.get(c):
                issues.append({"QuestionID": qid, "issue": "empty cell", "detail": c})

        opts = [q.get(f"Answer{n}", "") for n in range(1, 5)]
        nopts = [norm(o) for o in opts]
        dupes = {o for o in nopts if o and nopts.count(o) > 1}
        if dupes:
            issues.append({"QuestionID": qid, "issue": "duplicate answer options", "detail": sorted(dupes)})

        ca = q.get("CorrectAnswer", "")
        exact = [n + 1 for n, o in enumerate(opts) if o == ca]
        loose = [n + 1 for n, o in enumerate(nopts) if o == norm(ca)]
        q["correct_option"] = exact[0] if len(exact) == 1 else (loose[0] if len(loose) == 1 else None)
        if not loose:
            issues.append({"QuestionID": qid, "issue": "CorrectAnswer matches no option", "detail": ca})
        elif not exact:
            issues.append({"QuestionID": qid, "issue": "CorrectAnswer matches an option only after ignoring case/quotes/spacing",
                           "detail": {"CorrectAnswer": ca, "option": opts[loose[0] - 1]}})
        elif len(loose) > 1:
            issues.append({"QuestionID": qid, "issue": "CorrectAnswer matches more than one option", "detail": loose})

        ref = q.get("CodeReference", "")
        if regs and ref:
            for num in re.findall(r"\d+\.\d+", ref):
                if not re.search(rf"(^|\n)\s*{re.escape(num)}\s", regs):
                    issues.append({"QuestionID": qid, "issue": "CodeReference clause not found in regulation text",
                                   "detail": f"{ref} (looked for clause {num})"})
            for num, letter in re.findall(r"(\d+\.\d+)\s*\(([a-z])\)", ref):
                block = re.search(rf"(^|\n)\s*{re.escape(num)}\s(.*?)(?=\n\s*\d+\.\d+\s|\n\nSection|\Z)", regs, re.S)
                if block and not re.search(rf"(^|\s){letter}\)", block.group(2)):
                    issues.append({"QuestionID": qid, "issue": "CodeReference sub-item not found under clause",
                                   "detail": f"{ref} (no item {letter}) under {num})"})

    json.dump({"csv": csv_path, "columns": cols, "total_questions": len(questions),
               "questions": questions, "repairs": repairs, "issues": issues},
              sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
