import { useState } from "react";
import ResumeUpload from "./components/ResumeUpload";
import JobDescriptionInput from "./components/JobDescriptionInput";
import Results from "./components/Results";
import { matchResumeToJd } from "./api";
import "./App.css";

function App() {
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [matchResult, setMatchResult] = useState(null);
  const [isMatching, setIsMatching] = useState(false);
  const [matchError, setMatchError] = useState(null);

  async function handleRunMatch() {
    setIsMatching(true);
    setMatchError(null);
    setMatchResult(null);

    try {
      const result = await matchResumeToJd(resumeText, jdText);
      setMatchResult(result);
    } catch (err) {
      setMatchError(err.message);
    } finally {
      setIsMatching(false);
    }
  }

  const canRunMatch = resumeText.trim() && jdText.trim() && !isMatching;

  return (
    <div className="app">
      <h1>Resume ↔ JD Semantic Matcher</h1>
      <p className="hint">
        Runs entirely on your machine - no API keys, no cloud calls, no cost.
      </p>

      <ResumeUpload onResumeTextChange={setResumeText} />
      <JobDescriptionInput onJdTextChange={setJdText} />

      <div className="run-match-row">
        <button onClick={handleRunMatch} disabled={!canRunMatch}>
          {isMatching ? "Matching..." : "Run Match"}
        </button>
        {!canRunMatch && !isMatching && (
          <span className="hint">Add both a resume and a job description first.</span>
        )}
      </div>

      <Results result={matchResult} isLoading={isMatching} error={matchError} />
    </div>
  );
}

export default App;
