"""
Explaining match gaps using a local LLM (Ollama).

A cosine similarity score tells us THAT a JD requirement wasn't well
matched, but not WHY, or what's likely missing - that requires actual
reasoning about meaning, which is what we use a local LLM for here.
This is the only place in the whole pipeline that uses an LLM; everything
else (chunking, embeddings, similarity) is deterministic math.

Ollama runs entirely on your machine and exposes a local HTTP API at
http://localhost:11434 - no API key, no cloud call, no cost. You need
Ollama installed and the model pulled once:
    ollama pull llama3
"""

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# We ask for plain text, not JSON. Smaller local models are noticeably
# less reliable than hosted frontier models at producing strictly valid
# JSON - a broken JSON parse would crash this feature over something as
# low-stakes as a one-sentence explanation. Plain text has no parse step
# that can fail, so we just display whatever text comes back.
GAP_EXPLANATION_PROMPT_TEMPLATE = (
    "This job requirement was not well matched by a candidate's resume:\n"
    '"{jd_requirement}"\n\n'
    "In one short sentence, explain what skill or experience is likely "
    "missing from the resume. Be direct and specific."
)


def explain_gap(jd_requirement: str) -> str:
    """
    Ask the local Ollama server to explain, in one sentence, what's
    likely missing from the resume for a given weakly-matched JD
    requirement.

    If Ollama isn't running (e.g. it wasn't started, or isn't installed),
    we return a clear message instead of raising - a missing local LLM
    server shouldn't take down the whole matching feature, since the
    scores and matches are still useful on their own.
    """
    prompt = GAP_EXPLANATION_PROMPT_TEMPLATE.format(jd_requirement=jd_requirement)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.RequestException:
        return (
            "(Could not reach Ollama - make sure it's running locally at "
            "localhost:11434 and that you've run 'ollama pull llama3'.)"
        )
