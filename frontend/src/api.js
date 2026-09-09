// All calls to the local FastAPI backend, in one place. Every request
// goes to localhost - this app never talks to any server on the
// internet, which is the whole point of building it this way.

const API_BASE_URL = "http://localhost:8000";

/**
 * Upload a resume file (PDF or DOCX) and get back its extracted text.
 * Corresponds to the backend's POST /extract (Phase 1).
 */
export async function extractResumeText(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/extract`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || "Failed to extract text from file.");
  }

  return response.json(); // { filename, character_count, text }
}

/**
 * Run the full matching pipeline: chunk both texts, embed, score, and
 * get gap explanations back. Corresponds to POST /match (Phases 2-4).
 */
export async function matchResumeToJd(resumeText, jdText) {
  const response = await fetch(`${API_BASE_URL}/match`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_text: resumeText, jd_text: jdText }),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || "Failed to match resume to job description.");
  }

  return response.json(); // { overall_match_percent, matched, gaps }
}
