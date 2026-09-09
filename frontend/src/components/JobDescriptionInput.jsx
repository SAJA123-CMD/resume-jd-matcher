import { useState } from "react";

const API_BASE_URL = "http://localhost:8000";

/**
 * Section 2: job description input.
 *
 * We support two ways in: a URL (fetched server-side and scraped for
 * visible text) or pasting the JD text directly. The paste option isn't
 * a lesser fallback bolted on as an afterthought - it's there because
 * job sites vary hugely in how they build their pages. Some render the
 * posting straight into HTML we can read easily; others load it via
 * JavaScript after the page loads (which a simple server-side fetch
 * can't execute), or actively block scripted requests. Pasting text
 * always works, because if you can see it in your own browser, you can
 * copy it - so it's the one path guaranteed not to fail.
 */
export default function JobDescriptionInput({ onJdTextChange }) {
  const [mode, setMode] = useState("url"); // "url" or "paste"
  const [url, setUrl] = useState("");
  const [pastedText, setPastedText] = useState("");
  const [fetchedText, setFetchedText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleFetchUrl() {
    if (!url.trim()) return;
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/fetch-jd-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "Could not fetch that URL.");
      }

      const result = await response.json();
      setFetchedText(result.text);
      onJdTextChange(result.text);
    } catch (err) {
      setError(err.message);
      setFetchedText("");
      onJdTextChange("");
    } finally {
      setIsLoading(false);
    }
  }

  function handlePasteChange(event) {
    const text = event.target.value;
    setPastedText(text);
    onJdTextChange(text);
  }

  return (
    <section className="section">
      <h2>2. Add Job Description</h2>

      <div className="tab-row">
        <button
          className={mode === "url" ? "tab tab-active" : "tab"}
          onClick={() => setMode("url")}
        >
          Paste URL
        </button>
        <button
          className={mode === "paste" ? "tab tab-active" : "tab"}
          onClick={() => setMode("paste")}
        >
          Paste text instead
        </button>
      </div>

      {mode === "url" ? (
        <div>
          <div className="url-row">
            <input
              type="text"
              placeholder="https://example.com/job-posting"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <button onClick={handleFetchUrl} disabled={isLoading}>
              {isLoading ? "Fetching..." : "Fetch"}
            </button>
          </div>
          {error && (
            <p className="error">
              {error} Try the "Paste text instead" tab above.
            </p>
          )}
          {fetchedText && (
            <div>
              <p className="hint">Fetched text preview (job sites vary a lot - double check this looks right):</p>
              <textarea className="preview" value={fetchedText} readOnly rows={10} />
            </div>
          )}
        </div>
      ) : (
        <textarea
          className="preview"
          placeholder="Paste the job description text here..."
          value={pastedText}
          onChange={handlePasteChange}
          rows={10}
        />
      )}
    </section>
  );
}
