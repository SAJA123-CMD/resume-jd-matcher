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

# Matches common bullet markers at the start of a line (-, *, •, or "1.",
# "2)" etc.) so we can strip them before treating the rest as the chunk.
BULLET_PREFIX_PATTERN = re.compile(r"^[\-\*•]\s*|^\d+[\.\)]\s*")


def _split_into_candidate_lines(text: str) -> list[str]:
    """
    Break raw text into individual lines and strip bullet markers/whitespace.

    This is the same first step for both resumes and JDs - both are
    naturally bullet-heavy documents, so line-by-line splitting works for
    either one.
    """
    raw_lines = text.split("\n")
    cleaned_lines = []
    for line in raw_lines:
        without_bullet = BULLET_PREFIX_PATTERN.sub("", line.strip())
        cleaned_lines.append(without_bullet.strip())
    return cleaned_lines


def _filter_meaningful_lines(lines: list[str]) -> list[str]:
    """
    Drop lines that are too short to be a real, matchable statement.

    We deliberately leave these out of the embedding step entirely, rather
    than embedding everything - a section header like "SKILLS" has no
    real meaning to compare against a JD requirement, and would just add
    noise (or worse, accidentally "win" as a best-match by chance).
    """
    return [line for line in lines if len(line) >= MIN_CHUNK_LENGTH]


def chunk_resume_text(resume_text: str) -> list[str]:
    """
    Split resume text into chunks, one per bullet/line of real content.
    """
    lines = _split_into_candidate_lines(resume_text)
    return _filter_meaningful_lines(lines)


def chunk_jd_text(jd_text: str) -> list[str]:
    """
    Split job description text into chunks, one per requirement/bullet.

    Uses the same logic as resume chunking for now. JDs also tend to have
    boilerplate lines ("Job Type: Full-time", EEO statements) that are
    short enough to get filtered out naturally, but we may need smarter
    filtering here once we test on real, messy job postings scraped from
    URLs in a later phase.
    """
    lines = _split_into_candidate_lines(jd_text)
    return _filter_meaningful_lines(lines)
