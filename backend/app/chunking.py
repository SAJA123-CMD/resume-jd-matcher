"""
Splitting resume and JD text into meaningful chunks.

Phase 2 of the pipeline. We don't embed whole documents (too blurry - a
resume mixes many unrelated skills into one average meaning) and we don't
split by fixed character counts (that cuts sentences in half). Instead we
split by line/bullet, so each chunk is one complete, self-contained claim
("Led a team of 5 engineers...") that can be meaningfully compared against
a single JD requirement.
"""

import re

# Lines shorter than this are treated as noise rather than real content:
# section headers ("EXPERIENCE"), stray dates ("2019 - 2021"), or contact
# info. This is a blunt heuristic, not a precise rule - we'll tune this
# number after looking at real chunk output.
MIN_CHUNK_LENGTH = 15

# Matches common bullet markers at the start of a line: -, *, •, ⦁ (used by
# some job sites/Word exports), or numbered lists like "1." / "2)".
BULLET_PREFIX_PATTERN = re.compile(r"^[\-\*•⦁]\s*|^\d+[\.\)]\s*")


def _split_into_lines_with_bullet_info(text: str) -> list[tuple[str, bool]]:
    """
    Break raw text into lines, stripping bullet markers, and record
    whether each line originally had a bullet marker.

    We need to know "had a bullet" separately from the cleaned text
    because JD chunking uses it as a filter (see chunk_jd_text) - a real
    job requirement is almost always bulleted, while marketing/overview
    prose in a job posting usually isn't.
    """
    raw_lines = text.split("\n")
    result = []
    for line in raw_lines:
        stripped = line.strip()
        had_bullet = bool(BULLET_PREFIX_PATTERN.match(stripped))
        without_bullet = BULLET_PREFIX_PATTERN.sub("", stripped).strip()
        result.append((without_bullet, had_bullet))
    return result


def _is_meaningful(line: str) -> bool:
    """
    A line is "meaningful" if it's long enough to be a real statement,
    rather than a section header, stray date, or contact info fragment.
    """
    return len(line) >= MIN_CHUNK_LENGTH


def chunk_resume_text(resume_text: str) -> list[str]:
    """
    Split resume text into chunks, one per bullet/line of real content.

    Resumes are filtered by length only (not bullet presence) because
    resume formatting is inconsistent - plenty of real, valuable lines
    ("Led a team of 5 engineers...") appear with no bullet marker at all,
    e.g. under a job title as plain lines.
    """
    lines_with_bullets = _split_into_lines_with_bullet_info(resume_text)
    return [line for line, _ in lines_with_bullets if _is_meaningful(line)]


def chunk_jd_text(jd_text: str) -> list[str]:
    """
    Split job description text into chunks, one per requirement/bullet.

    We first try requiring a bullet marker, since real job postings almost
    always list actual requirements as bullets while surrounding "why work
    here" marketing paragraphs and job titles are plain prose - this was
    confirmed on a real JD in testing, where it correctly dropped title/
    marketing lines that would otherwise have polluted matching.

    However, pasted JD text doesn't always keep its bullet characters -
    copying from a browser can lose them, leaving plain lines with real
    requirement content but no bullet marker at all. If bullet-filtering
    would leave us with zero chunks, that's a sign this particular JD
    doesn't use bullets we can detect, so we fall back to length-only
    filtering (same rule as resumes) rather than returning nothing.
    """
    lines_with_bullets = _split_into_lines_with_bullet_info(jd_text)

    bulleted_chunks = [
        line
        for line, had_bullet in lines_with_bullets
        if had_bullet and _is_meaningful(line)
    ]
    if bulleted_chunks:
        return bulleted_chunks

    return [line for line, _ in lines_with_bullets if _is_meaningful(line)]
