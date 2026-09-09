"""
Manual test helper for Phase 3 (embeddings + similarity matching).

Reads a resume .txt file and a JD .txt file, chunks both, embeds both,
and prints each JD requirement next to its best-matching resume chunk
and the similarity score - so you can sanity-check by eye whether the
"best matches" actually look related to a human reader.

Usage:
    python scripts/preview_matches.py path/to/resume.txt path/to/jd.txt
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunking import chunk_resume_text, chunk_jd_text
from app.matching import find_best_matches


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/preview_matches.py <resume.txt> <jd.txt>")
        sys.exit(1)

    resume_text = Path(sys.argv[1]).read_text(encoding="utf-8")
    jd_text = Path(sys.argv[2]).read_text(encoding="utf-8")

    resume_chunks = chunk_resume_text(resume_text)
    jd_chunks = chunk_jd_text(jd_text)

    print(f"\n{len(resume_chunks)} resume chunks, {len(jd_chunks)} JD chunks\n")
    print("Loading model and computing similarity (first run downloads the model)...\n")

    results = find_best_matches(resume_chunks, jd_chunks)

    # Sort so the strongest matches show first - easiest to sanity-check
    # the high end and the low end of the score range at a glance.
    results.sort(key=lambda r: r["score"], reverse=True)

    for result in results:
        print(f"Score: {result['score']}")
        print(f"  JD requirement: {result['jd_requirement']}")
        print(f"  Best resume match: {result['best_match']}")
        print()


if __name__ == "__main__":
    main()
