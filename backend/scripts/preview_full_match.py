"""
Manual test helper for Phase 4 (full pipeline: matches + gap analysis).

Reads a resume .txt file and a JD .txt file, runs the entire pipeline
(chunk -> embed -> match -> split into matched/gaps -> explain gaps via
Ollama), and prints the result the way the API would return it.

Requires Ollama running locally (ollama serve, usually started
automatically) with the model pulled:
    ollama pull llama3

Usage:
    python scripts/preview_full_match.py path/to/resume.txt path/to/jd.txt
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunking import chunk_resume_text, chunk_jd_text
from app.matching import find_best_matches, split_matches_and_gaps
from app.gap_analysis import explain_gap


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/preview_full_match.py <resume.txt> <jd.txt>")
        sys.exit(1)

    resume_text = Path(sys.argv[1]).read_text(encoding="utf-8")
    jd_text = Path(sys.argv[2]).read_text(encoding="utf-8")

    resume_chunks = chunk_resume_text(resume_text)
    jd_chunks = chunk_jd_text(jd_text)

    print(f"\n{len(resume_chunks)} resume chunks, {len(jd_chunks)} JD chunks")
    print("Computing similarity...\n")

    matches = find_best_matches(resume_chunks, jd_chunks)
    matched, gaps = split_matches_and_gaps(matches)

    overall_match_percent = round(100 * len(matched) / len(jd_chunks))
    print(f"=== Overall match: {overall_match_percent}% ({len(matched)}/{len(jd_chunks)} requirements) ===\n")

    print(f"--- MATCHED ({len(matched)}) ---\n")
    for m in matched:
        print(f"[{m['score']}] {m['jd_requirement']}")
        print(f"    -> {m['best_match']}\n")

    print(f"--- GAPS ({len(gaps)}) - asking Ollama to explain each one ---\n")
    for gap in gaps:
        explanation = explain_gap(gap["jd_requirement"])
        print(f"[{gap['score']}] {gap['jd_requirement']}")
        print(f"    Gap: {explanation}\n")


if __name__ == "__main__":
    main()
