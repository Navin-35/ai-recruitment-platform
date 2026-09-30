import React, { useState } from "react";
import { Users, UploadCloud, Search } from "lucide-react";
import CandidateTable from "../components/CandidateTable";
import ResumeUploader from "../components/ResumeUploader";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";

export const Candidates = ({
  candidates = [],
  loading = false,
  error = null,
  onSelectCandidate,
  onCandidateCreated,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [showUploader, setShowUploader] = useState(false);

  if (loading) return <LoadingState message="Loading candidate profiles..." rows={5} />;
  if (error) return <ErrorState message={error} />;

  const filteredCandidates = candidates.filter((c) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      c.name?.toLowerCase().includes(term) ||
      c.skills?.toLowerCase().includes(term) ||
      c.email?.toLowerCase().includes(term)
    );
  });

  return (
    <div className="page-candidates">
      <div className="page-header-row">
        <div>
          <h2 className="page-title">Candidate Pool</h2>
          <p className="page-subtitle">
            Profiles extracted with section-aware chunking and verified document evidence.
          </p>
        </div>
        <button
          onClick={() => setShowUploader(!showUploader)}
          className="btn-primary"
        >
          <UploadCloud size={16} className="icon-mr" />
          {showUploader ? "Hide Uploader" : "Ingest New Resumes"}
        </button>
      </div>

      {showUploader && (
        <div className="uploader-drawer">
          <ResumeUploader
            candidates={candidates}
            onUploadComplete={(candId) => {
              if (onCandidateCreated) onCandidateCreated(candId);
              setShowUploader(false);
            }}
          />
        </div>
      )}

      {/* Search Bar */}
      <div className="search-filter-card">
        <div className="search-input-wrapper">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search candidates by name, skill, email, or experience keywords..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="filter-search-input"
          />
        </div>
        <div className="results-count-text">
          Showing <strong>{filteredCandidates.length}</strong> of {candidates.length} candidates
        </div>
      </div>

      {/* Candidate Table */}
      <div className="candidates-table-container">
        <CandidateTable
          candidates={filteredCandidates}
          onSelectCandidate={onSelectCandidate}
        />
      </div>
    </div>
  );
};

export default Candidates;
