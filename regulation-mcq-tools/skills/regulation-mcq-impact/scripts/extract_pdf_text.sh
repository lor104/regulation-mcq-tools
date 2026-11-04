#!/usr/bin/env bash
# Extract text from a regulations PDF and normalize it so each section heading,
# numbered clause (1.1, 4.2 ...) and lettered sub-item (a), b) ...) is on its own line.
# Usage: extract_pdf_text.sh <file.pdf>  (writes to stdout)
set -euo pipefail
pdf="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"

raw() {
  if command -v pdftotext >/dev/null 2>&1; then
    pdftotext "$pdf" -
  elif [[ "$(uname)" == "Darwin" ]]; then
    osascript -l JavaScript -e '
ObjC.import("PDFKit");
function run(argv){ return $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0])).string.js; }' "$pdf"
  else
    python3 -I -c 'import sys,pypdf; print("\n".join(p.extract_text() or "" for p in pypdf.PdfReader(sys.argv[1]).pages))' "$pdf"
  fi
}

raw | tr '\n' ' ' | sed -E \
  -e 's/  +/ /g' \
  -e 's/ (Section [0-9]+ –)/\n\n\1/g' \
  -e 's/ ?([0-9]+\.[0-9]+ [A-Z“"])/\n\1/g' \
  -e 's/ ([a-z]\) )/\n   \1/g'
echo
