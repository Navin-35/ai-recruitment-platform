import React from "react";
import { ArrowLeft } from "lucide-react";
import JobForm from "../components/JobForm";

export const CreateJob = ({ onJobCreated, onNavigateBack }) => {
  return (
    <div className="page-create-job">
      <div className="page-header-row">
        <button onClick={onNavigateBack} className="btn-secondary btn-sm">
          <ArrowLeft size={14} className="icon-mr" /> Back to Jobs
        </button>
      </div>

      <div className="create-job-container">
        <div className="create-job-intro">
          <h2 className="page-title">New Job Description</h2>
          <p className="page-subtitle">
            Provide the job description via raw text or upload a document (.pdf, .docx).
            The platform will automatically parse responsibilities, extract mandatory vs preferred competencies,
            normalize requirements via the Skill Graph, and generate 768-dim embeddings.
          </p>
        </div>

        <JobForm
          onJobCreated={(job) => {
            if (onJobCreated) onJobCreated(job);
          }}
        />
      </div>
    </div>
  );
};

export default CreateJob;
