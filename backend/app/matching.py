"""
Embedding resume/JD chunks and matching them by cosine similarity.

Phase 3 of the pipeline - this is the core "semantic" part of the tool.

What's an embedding? The model below reads a sentence and outputs a fixed
-length list of 384 numbers - a vector - that represents the sentence's
*meaning* in a mathematical space. Sentences with similar meaning end up
as vectors pointing in a similar direction, even when they share no words
at all: "led a team of 5 engineers" and "managed a small engineering
team" land close together, while "led a team of 5 engineers" and
"proficient in Excel" land far apart.

What's cosine similarity? It measures the angle between two vectors,
ignoring their length/magnitude - so it captures "do these point in the
same direction" (same meaning) rather than "are these numbers big or
small" (which can vary for reasons unrelated to meaning, like sentence
length). For this model, cosine similarity output is roughly in the
range 0 (unrelated meaning) to 1 (near-identical meaning).
"""

from sentence_transformers import SentenceTransformer, util

# JD requirements whose best resume match scores below this are treated
# as "gaps" needing an LLM explanation (Phase 4), rather than a genuine
# match. Chosen empirically from real test runs: on all-MiniLM-L6-v2,
# short technical bullet points tend to score lower overall than full
# natural-language sentences would (even a strong match often lands
# around 0.5-0.6 rather than 0.8-0.9), so 0.45 was picked to catch clearly
# weak matches (visa boilerplate, "collaborative spirit") without
# flagging reasonable-if-imperfect matches as gaps. This is a starting
# point, not a precise science - if real test runs show it's too
# aggressive or too lax, adjust this one number.
GAP_THRESHOLD = 0.45

# Loading the model reads ~80MB of weights from disk (downloaded once,
# the first time this runs, and cached locally after that - no API key,
# no network call on later runs). We load it once at import time rather
# than per-request, since loading it is the slow part and the model
# itself doesn't change between requests.
_model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_chunks(chunks: list[str]):
    """
    Turn a list of text chunks into a matrix of embedding vectors.

    Input: ["chunk one", "chunk two", ...]  (N chunks)
    Output: a tensor of shape (N, 384) - one 384-number vector per chunk.

    Embedding a whole list at once (rather than one-by-one in a loop) lets
    sentence-transformers batch the work internally, which is both faster
    and simpler to call.
    """
    return _model.encode(chunks, convert_to_tensor=True)


def find_best_matches(resume_chunks: list[str], jd_chunks: list[str]) -> list[dict]:
    """
    For every JD chunk, find the resume chunk that's the closest semantic
    match, using cosine similarity.

    We compute this as one similarity matrix rather than a nested loop:
    resume_embeddings is (R, 384), jd_embeddings is (J, 384), and
    util.cos_sim gives us every pairwise similarity at once as a (J, R)
    matrix - row i, column j is "how similar is JD chunk i to resume
    chunk j". A nested Python loop computing one pair at a time would give
    the identical numbers, just slower and with more code - the matrix
    form is the standard way this library is used, so we go with that.

    Returns a list of dicts, one per JD chunk:
        {"jd_requirement": ..., "best_match": ..., "score": ...}
    """
    resume_embeddings = embed_chunks(resume_chunks)
    jd_embeddings = embed_chunks(jd_chunks)

    # similarity_matrix[i][j] = cosine similarity between jd_chunks[i]
    # and resume_chunks[j]
    similarity_matrix = util.cos_sim(jd_embeddings, resume_embeddings)

    results = []
    for jd_index, jd_requirement in enumerate(jd_chunks):
        row = similarity_matrix[jd_index]
        best_resume_index = int(row.argmax())
        best_score = float(row[best_resume_index])

        results.append(
            {
                "jd_requirement": jd_requirement,
                "best_match": resume_chunks[best_resume_index],
                "score": round(best_score, 3),
            }
        )

    return results


def split_matches_and_gaps(matches: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Split match results into "matched" (score >= GAP_THRESHOLD) and
    "gaps" (score below it), based purely on the threshold above.

    Kept separate from find_best_matches so the threshold logic is easy
    to find/change independently of the similarity computation itself.
    """
    matched = [m for m in matches if m["score"] >= GAP_THRESHOLD]
    gaps = [m for m in matches if m["score"] < GAP_THRESHOLD]
    return matched, gaps
