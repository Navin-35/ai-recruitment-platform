import React, { useState } from "react";
import { Briefcase, Upload, FileText, Sparkles, Loader2, AlertCircle } from "lucide-react";
import { createJob, uploadJobFile, extractJobRequirements } from "../services/jobs";

export const JobForm = ({ onJobCreated }) => {
  const [activeTab, setActiveTab] = useState("text"); // 'text' or 'file'
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setError(null);

      let createdJob = null;

      if (activeTab === "file") {
        if (!file) {
          setError("Please select a Job Description document (PDF, DOCX, or TXT).");
          setSubmitting(false);
          return;
        }
        const formData = new FormData();
        formData.append("file", file);
        if (title) formData.append("title", title);
        if (company) formData.append("company_name", company);
        if (location) formData.append("location", location);

        createdJob = await uploadJobFile(formData);
      } else {
        if (!title.trim() || !description.trim()) {
          setError("Job title and job description are required.");
          setSubmitting(false);
          return;
        }
        createdJob = await createJob({
          title,
          company_name: company || null,
          location: location || null,
          description,
        });

        // Automatically trigger AI extraction of atomic requirements
        try {
          createdJob = await extractJobRequirements(createdJob.id);
        } catch (extractErr) {
          console.warn("Requirements will be decomposed during first match:", extractErr);
        }
      }

      if (onJobCreated) {
        onJobCreated(createdJob);
      }
    } catch (err) {
      setError(err.message || "Failed to create job posting.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="job-form-card">
      <div className="job-form-header">
        <h4 className="card-heading">
          <Briefcase size={18} className="icon-mr" /> Create & Decompose Job Description
        </h4>
        <div className="tab-pill-group">
          <button
            type="button"
            className={`tab-pill ${activeTab === "text" ? "active" : ""}`}
            onClick={() => setActiveTab("text")}
          >
            Raw Text
          </button>
          <button
            type="button"
            className={`tab-pill ${activeTab === "file" ? "active" : ""}`}
            onClick={() => setActiveTab("file")}
          >
            Upload File (PDF/DOCX)
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="job-entry-form">
        <div className="form-row-2">
          <div className="form-group">
            <label className="form-label">Job Title *</label>
            <input
              type="text"
              placeholder="e.g. Senior Backend Engineer"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="form-input"
              required={activeTab === "text"}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Company Name</label>
            <input
              type="text"
              placeholder="e.g. Acme Cloud Systems"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="form-input"
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Location / Remote Policy</label>
          <input
            type="text"
            placeholder="e.g. San Francisco, CA / Remote"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="form-input"
          />
        </div>

        {activeTab === "text" ? (
          <div className="form-group">
            <label className="form-label">Job Description & Requirements *</label>
            <textarea
              rows={8}
              placeholder="Paste full job description including responsibilities, required technical skills, years of experience, and nice-to-haves..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="form-textarea"
              required
            />
          </div>
        ) : (
          <div className="file-dropzone">
            <input
              type="file"
              id="job-file-input"
              accept=".pdf,.docx,.txt"
              onChange={(e) => e.target.files && setFile(e.target.files[0])}
              className="file-hidden-input"
            />
            <label htmlFor="job-file-input" className="file-dropzone-label">
              <Upload size={32} className="dropzone-icon" />
              <span className="dropzone-text">
                {file ? file.name : "Select Job Description Document (.pdf, .docx, .txt)"}
              </span>
              <span className="dropzone-hint">AI will extract and vectorize all atomic requirements</span>
            </label>
          </div>
        )}

        {error && (
          <div className="alert-inline alert-error">
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="btn-primary btn-full-width"
        >
          {submitting ? (
            <>
              <Loader2 size={16} className="animate-spin icon-mr" />
              Decomposing Requirements with Gemini...
            </>
          ) : (
            <>
              <Sparkles size={16} className="icon-mr" /> Create & Decompose Requirements
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default JobForm;
