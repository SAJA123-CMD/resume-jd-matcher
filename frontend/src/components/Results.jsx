/**
 * Section 3: results.
 *
 * Shows the overall match score, then two lists: requirements that
 * matched well (with the resume line that matched them, as evidence),
 * and gaps (requirements that didn't match well, with a plain-English
 * explanation of what's likely missing or weaker).
 */
export default function Results({ result, isLoading, error }) {
  if (isLoading) {
    return (
      <section className="section">
        <h2>3. Results</h2>
        <p>Matching resume against job description... (this can take a little while, especially the first time, while Ollama generates gap explanations)</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="section">
        <h2>3. Results</h2>
        <p className="error">{error}</p>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="section">
        <h2>3. Results</h2>
        <p className="hint">Add a resume and a job description above, then click "Run Match" to see results here.</p>
      </section>
    );
  }

  const { overall_match_percent, matched, gaps } = result;

  return (
    <section className="section">
      <h2>3. Results</h2>

      <div className="score">{overall_match_percent}% match</div>
      <p className="hint">
        {matched.length} of {matched.length + gaps.length} requirements matched well
      </p>

      <h3>Matching ({matched.length})</h3>
      {matched.length === 0 && <p className="hint">No strong matches found.</p>}
      <ul className="result-list">
        {matched.map((item, index) => (
          <li key={index} className="result-item">
            <div className="requirement">{item.jd_requirement}</div>
            <div className="evidence">Resume evidence: "{item.best_match}"</div>
            <div className="score-tag">score: {item.score}</div>
          </li>
        ))}
      </ul>

      <h3>Gaps ({gaps.length})</h3>
      {gaps.length === 0 && <p className="hint">No gaps found.</p>}
      <ul className="result-list">
        {gaps.map((item, index) => (
          <li key={index} className="result-item result-item-gap">
            <div className="requirement">{item.jd_requirement}</div>
            <div className="evidence">{item.explanation}</div>
            <div className="score-tag">score: {item.score}</div>
          </li>
        ))}
      </ul>
    </section>
  );
}
