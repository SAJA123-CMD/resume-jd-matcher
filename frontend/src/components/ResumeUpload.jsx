import { useState } from "react";
import { extractResumeText } from "../api";

/**
 * Section 1: resume upload.
 *
 * We show the extracted text back to the user after upload, not just a
 * success message - Phase 1 taught us that PDF/DOCX parsing can silently
 * go wrong (missing sections, garbled text), and the best way to catch
 * that is letting a human glance at what actually got extracted.
 */
export default function ResumeUpload({ onResumeTextChange }) {
  const [fileName, setFileName] = useState(null);
  const [extractedText, setExtractedText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isDraggingOver, setIsDraggingOver] = useState(false);

  async function handleFile(file) {
    if (!file) return;
    setIsLoading(true);
    setError(null);
    setFileName(file.name);

    try {
      const result = await extractResumeText(file);
      setExtractedText(result.text);
      onResumeTextChange(result.text);
    } catch (err) {
      setError(err.message);
      setExtractedText("");
      onResumeTextChange("");
    } finally {
      setIsLoading(false);
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDraggingOver(false);
    handleFile(event.dataTransfer.files[0]);
  }

  return (
    <section className="section">
      <h2>1. Attach Resume</h2>

      <label
        className={`dropzone ${isDraggingOver ? "dropzone-active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDraggingOver(true);
        }}
        onDragLeave={() => setIsDraggingOver(false)}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={(e) => handleFile(e.target.files[0])}
          hidden
        />
        {fileName ? (
          <span>{fileName}</span>
        ) : (
          <span>Drag and drop a PDF or DOCX resume here, or click to choose a file</span>
        )}
      </label>

      {isLoading && <p>Extracting text...</p>}
      {error && <p className="error">{error}</p>}

      {extractedText && (
        <div>
          <p className="hint">Extracted text preview (confirm this looks right before continuing):</p>
          <textarea
            className="preview"
            value={extractedText}
            readOnly
            rows={10}
          />
        </div>
      )}
    </section>
  );
}
