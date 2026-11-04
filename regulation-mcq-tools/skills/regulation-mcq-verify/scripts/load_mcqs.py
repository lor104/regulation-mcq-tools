#!/usr/bin/env python3
"""Load an MCQ CSV, repair line breaks inside cells, and run structural checks.

Usage:
  python3 -I load_mcqs.py <questions.csv> [<regulations.txt>] > <scratch>/mcqs.json

- Reads the CSV with a real CSV parser (cells may contain line breaks).
- Repairs line breaks inside cells. A break is removed when the text on both sides
  forms a word found in the regulation text ("organization\n s" -> "organizations"),
  when neither side is a word in the regulation text and the right side is a short
  lowercase fragment ("Ju\n ne" -> "June"), or when it sits next to punctuation
  ("Trespassing\n ”"). Otherwise it becomes a space. Every repair is listed so it
  can be double-checked.
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
BREAK = re.compile(r"[ \t]*(?:\r?\n[ \t]*)+")
CLOSING = set("”’\"')]}.,;:!?")
OPENING = set("“‘\"'([{")


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

    def fix(qid, col, text, row_lines=()):
        # Each break is judged on the text around it in the original cell, so a
        # cell with several breaks in a row ("organization\n s keeping\n bees")
        # and fragments next to punctuation ("March–Octo\n ber") are handled.
        # The best evidence is the same row: the CorrectAnswer repeats an option,
        # and the two cells often break in different places.
        def in_row(phrase):
            pat = re.compile(rf"(?<![A-Za-z]){re.escape(phrase)}(?![A-Za-z])", re.I)
            return any(pat.search(line) for line in row_lines)

        def repl(m):
            before, after = m.string[:m.start()], m.string[m.end():]
            left = re.search(r"\S*$", before).group()
            right = re.match(r"\S*", after).group()
            lw = re.search(r"[A-Za-z]+$", before)
            rw = re.match(r"[A-Za-z]+", after)
            if not before or not after:
                sep, how = "", "removed (edge of cell)"
            elif after[0] in CLOSING or before[-1] in OPENING:
                sep, how = "", "removed (next to punctuation)"
            elif lw and rw:
                a, b = lw.group(), rw.group()
                a_word, b_word = a.casefold() in vocab, b.casefold() in vocab
                if in_row(a + " " + b):
                    sep, how = " ", "replaced with space (written with a space elsewhere in the row)"
                elif in_row(a + b):
                    sep, how = "", "joined (written as one word elsewhere in the row)"
                elif (a + b).casefold() in vocab and not (a_word and b_word):
                    sep, how = "", "joined (word found in regulations)"
                elif vocab and not a_word and not b_word and b.islower() and len(b) <= 4:
                    sep, how = "", "joined (neither fragment is a word in the regulations; verify)"
                elif not vocab:
                    sep, how = " ", "replaced with space (no regulation text given; verify)"
                else:
                    sep, how = " ", "replaced with space"
            else:
                sep, how = " ", "replaced with space"
            repairs.append({"QuestionID": qid, "column": col,
                            "before": left + "\\n" + right, "after": left + sep + right, "how": how})
            return sep
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
        row_lines = [ln.strip() for v in r.values() for ln in re.split(r"\r?\n", v)]
        for c in cols:
            q[c] = fix(qid, c, r.get(c, ""), row_lines).strip()
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
