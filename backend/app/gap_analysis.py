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
#
# Crucially, we pass the best resume match we DID find (even though it
# scored below the gap threshold) rather than just the JD requirement
# alone. Without this, the LLM has no idea the resume has anything
# related at all, and tends to claim skills are "completely missing"
# even when a real, if imperfect, match exists (e.g. a JD asking for "a
# Bachelor's degree" scoring 0.38 against a resume line that says
# "Bachelor of Computer Science" - a real match, just not a highly
# -scoring one). Giving the LLM that context lets it reason about
# "what's weaker or missing given this" instead of guessing blind.
GAP_EXPLANATION_PROMPT_TEMPLATE = (
    "A job requirement was compared against a candidate's resume. The "
    "closest related statement found in the resume is shown below, but "
    "it was not considered a strong match (similarity score {score} out "
    "of 1.0).\n\n"
    'Job requirement: "{jd_requirement}"\n'
    'Closest resume statement found: "{best_match}"\n\n'
    "In one short sentence, explain what is specifically missing or "
    "weaker in the resume compared to the full job requirement. If the "
    "resume statement is actually a reasonable match despite the low "
    "score, say so instead of inventing a gap."
)


def explain_gap(jd_requirement: str, best_match: str, score: float) -> str:
    """
    Ask the local Ollama server to explain, in one sentence, what's
    specifically missing or weaker in the resume for a given weakly
    -matched JD requirement - given the best resume statement we did
    find, so the LLM isn't guessing blind about what the resume contains.

    If Ollama isn't running (e.g. it wasn't started, or isn't installed),
    we return a clear message instead of raising - a missing local LLM
    server shouldn't take down the whole matching feature, since the
    scores and matches are still useful on their own.
    """
    prompt = GAP_EXPLANATION_PROMPT_TEMPLATE.format(
        jd_requirement=jd_requirement, best_match=best_match, score=score
    )

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
