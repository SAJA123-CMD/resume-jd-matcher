"""
FastAPI app for the Resume <-> JD Semantic Matcher.

Phase 1: a single endpoint that accepts a resume file (PDF or DOCX) and
returns the raw extracted text, so we can manually sanity-check parsing
quality before building chunking/embedding/matching on top of it.
"""

import logging

import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.extraction import extract_text
from app.chunking import chunk_resume_text, chunk_jd_text
from app.matching import find_best_matches, split_matches_and_gaps
from app.gap_analysis import explain_gap
from app.jd_fetcher import fetch_jd_text_from_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume <-> JD Semantic Matcher")

# The React dev server runs on a different port (5173) than the API (8000).
# Browsers block cross-origin requests by default, so we explicitly allow
# the frontend's origin here. This is purely a local-dev convenience -
# nothing about this app talks to the internet.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Simple liveness check - useful for confirming the server is up."""
    return {"status": "ok"}


@app.post("/extract")
async def extract_resume_text(file: UploadFile = File(...)):
    """
    Accept an uploaded PDF or DOCX file and return its extracted text.

    This is intentionally the entire endpoint for Phase 1 - no chunking,
    no embeddings. We want to look at real extracted text from real
    resumes before deciding how to split it up.
    """
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = extract_text(file.filename, file_bytes)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if not text.strip():
        # Most common cause: a scanned/image-only PDF with no text layer.
        raise HTTPException(
            status_code=422,
            detail=(
                "No text could be extracted from this file. If it's a PDF, "
                "it may be a scanned image without a text layer."
            ),
        )

    return {
        "filename": file.filename,
        "character_count": len(text),
        "text": text,
    }


class FetchJdUrlRequest(BaseModel):
    url: str


@app.post("/fetch-jd-url")
def fetch_jd_url(request: FetchJdUrlRequest):
    """
    Best-effort fetch of a job posting's visible text from a URL.

    Job sites vary hugely in HTML structure, and some block scripted
    requests or render content via JavaScript we can't execute here - so
    this can fail or return messy text. That's why the frontend always
    offers a "paste text instead" fallback: this endpoint is a
    convenience, not something the app depends on working every time.
    """
    try:
        text = fetch_jd_text_from_url(request.url)
    except requests.RequestException as error:
        raise HTTPException(
            status_code=422,
            detail=f"Could not fetch that URL: {error}. Try pasting the JD text instead.",
        )

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from that page. Try pasting the JD text instead.",
        )

    return {"text": text}


class ChunkRequest(BaseModel):
    text: str
    kind: str  # "resume" or "jd" - determines which chunking rules to apply


@app.post("/chunk")
def chunk_text(request: ChunkRequest):
    """
    Phase 2 test endpoint: split raw text into chunks and return them.

    This exists purely so we can manually sanity-check the chunking logic
    on real resume/JD text before wiring embeddings on top of it. The
    chunks are also logged server-side so you can see them in the
    terminal running uvicorn, not just in the JSON response.
    """
    if request.kind == "resume":
        chunks = chunk_resume_text(request.text)
    elif request.kind == "jd":
        chunks = chunk_jd_text(request.text)
    else:
        raise HTTPException(status_code=400, detail="kind must be 'resume' or 'jd'")

    logger.info("Chunked %s text into %d chunks:", request.kind, len(chunks))
    for index, chunk in enumerate(chunks):
        logger.info("  [%d] %s", index, chunk)

    return {"chunk_count": len(chunks), "chunks": chunks}


class MatchRequest(BaseModel):
    resume_text: str
    jd_text: str


@app.post("/match")
def match_resume_to_jd(request: MatchRequest):
    """
    The full pipeline in one call: chunk both texts, embed them, find the
    best resume match for every JD requirement, split results into solid
    matches vs. gaps by score, and ask the local Ollama LLM to explain
    each gap in one sentence.

    Returns everything the frontend needs to render all three result
    sections: overall match %, the matched list (with resume evidence),
    and the gaps list (with a plain-English explanation of what's likely
    missing).
    """
    resume_chunks = chunk_resume_text(request.resume_text)
    jd_chunks = chunk_jd_text(request.jd_text)

    if not resume_chunks:
        raise HTTPException(status_code=400, detail="No resume chunks found.")
    if not jd_chunks:
        raise HTTPException(status_code=400, detail="No JD chunks found.")

    matches = find_best_matches(resume_chunks, jd_chunks)
    matched, gaps = split_matches_and_gaps(matches)

    logger.info(
        "Matched %d/%d JD requirements (%d gaps)", len(matched), len(jd_chunks), len(gaps)
    )

    # Only the gaps need an LLM call - matched requirements already have
    # their resume evidence, which is explanation enough.
    for gap in gaps:
        gap["explanation"] = explain_gap(
            gap["jd_requirement"], gap["best_match"], gap["score"]
        )
        logger.info("  gap: '%s' -> %s", gap["jd_requirement"], gap["explanation"])

    overall_match_percent = round(100 * len(matched) / len(jd_chunks))

    return {
        "overall_match_percent": overall_match_percent,
        "matched": matched,
        "gaps": gaps,
    }
