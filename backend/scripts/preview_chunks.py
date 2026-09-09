"""
Manual test helper for Phase 2 (chunking).

Reads a plain .txt file and prints the resulting chunks, so you can
sanity-check chunking on a real resume or JD without needing to paste
multi-line text into a JSON request (which is fiddly - JSON strings can't
contain literal newlines, only escaped \\n).

Usage:
    python scripts/preview_chunks.py path/to/resume.txt resume
    python scripts/preview_chunks.py path/to/jd.txt jd

Tip: to get a .txt file for your resume, copy the "text" value out of the
/extract endpoint's response and paste it into a plain text file. For a
JD, just copy the job posting text straight from the browser into a
.txt file.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunking import chunk_resume_text, chunk_jd_text


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in ("resume", "jd"):
        print("Usage: python scripts/preview_chunks.py <path_to_txt_file> <resume|jd>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    kind = sys.argv[2]

    text = file_path.read_text(encoding="utf-8")
    chunker = chunk_resume_text if kind == "resume" else chunk_jd_text
    chunks = chunker(text)

    print(f"\n{len(chunks)} chunks found:\n")
    for index, chunk in enumerate(chunks):
        print(f"[{index}] {chunk}")
    print()


if __name__ == "__main__":
    main()
