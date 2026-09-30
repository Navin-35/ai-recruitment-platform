import React, { useState } from "react";
import { UploadCloud, CheckCircle2, AlertCircle, FileText, Loader2 } from "lucide-react";
import { createCandidate } from "../services/candidates";
import { uploadResume, processResume } from "../services/resumes";

export const ResumeUploader = ({ candidates = [], onUploadComplete }) => {
  const [selectedCandidateId, setSelectedCandidateId] = useState("");
  const [newCandidateName, setNewCandidateName] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusStep, setStatusStep] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please choose a PDF or DOCX resume file.");
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setSuccess(false);

      let candidateId = selectedCandidateId;

      // Create new candidate if none selected
      if (!candidateId) {
        setStatusStep("Registering candidate profile...");
        setProgress(20);
        const nameToUse = newCandidateName.trim() || file.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ");
        const newCandidate = await createCandidate({ name: nameToUse });
        candidateId = newCandidate.id;
      }

      // Upload file to backend / storage
      setStatusStep("Uploading document to private storage...");
      setProgress(45);
      const resumeRecord = await uploadResume(candidateId, file);

      // Process via AI pipeline
      setStatusStep("Gemini parsing, section-aware chunking & embedding...");
      setProgress(75);
      await processResume(resumeRecord.id);

      setProgress(100);
      setStatusStep("Resume parsed and indexed successfully!");
      setSuccess(true);
      setFile(null);
      setNewCandidateName("");

      if (onUploadComplete) {
        onUploadComplete(candidateId);
      }
    } catch (err) {
      setError(err.message || "Failed to process resume.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="resume-uploader-card">
      <h4 className="card-heading">
        <UploadCloud size={18} className="icon-mr" /> Ingest Candidate Resume
      </h4>
      <p className="card-subtext">
        Upload PDF or DOCX resumes. The AI pipeline extracts profiles, normalizes skills, and indexes section chunks with page citations.
      </p>

      <form onSubmit={handleUpload} className="uploader-form">
        <div className="form-group">
          <label className="form-label">Associate with Candidate (Optional):</label>
          <select
            value={selectedCandidateId}
            onChange={(e) => setSelectedCandidateId(e.target.value)}
            className="form-select"
            disabled={uploading}
          >
            <option value="">+ Create New Candidate from Resume</option>
            {candidates.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name || `Candidate #${c.id}`} ({c.email || "No email"})
              </option>
            ))}
          </select>
        </div>

        {!selectedCandidateId && (
          <div className="form-group">
            <label className="form-label">Candidate Name (Optional):</label>
            <input
              type="text"
              placeholder="Will auto-extract from resume if blank"
              value={newCandidateName}
              onChange={(e) => setNewCandidateName(e.target.value)}
              className="form-input"
              disabled={uploading}
            />
          </div>
        )}

        <div className="file-dropzone">
          <input
            type="file"
            id="resume-file-input"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            className="file-hidden-input"
            disabled={uploading}
          />
          <label htmlFor="resume-file-input" className="file-dropzone-label">
            <FileText size={32} className="dropzone-icon" />
            <span className="dropzone-text">
              {file ? file.name : "Drag & drop resume or click to browse (PDF, DOCX)"}
            </span>
            <span className="dropzone-hint">Max file size: 10MB</span>
          </label>
        </div>

        {uploading && (
          <div className="upload-progress-wrapper">
            <div className="progress-bar-container">
              <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
            </div>
            <div className="progress-status-row">
              <span className="progress-step-text">{statusStep}</span>
              <span className="progress-percentage">{progress}%</span>
            </div>
          </div>
        )}

        {error && (
          <div className="alert-inline alert-error">
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="alert-inline alert-success">
            <CheckCircle2 size={15} />
            <span>Candidate profile extracted and vector-indexed!</span>
          </div>
        )}

        <button
          type="submit"
          disabled={!file || uploading}
          className="btn-primary btn-full-width"
        >
          {uploading ? (
            <>
              <Loader2 size={16} className="animate-spin icon-mr" /> Processing Document...
            </>
          ) : (
            "Upload & Run AI Extraction"
          )}
        </button>
      </form>
    </div>
  );
};

export default ResumeUploader;
