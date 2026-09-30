import React, { useState } from "react";
import { PlusCircle, Search, Filter } from "lucide-react";
import JobCard from "../components/JobCard";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";

export const Jobs = ({
  jobs = [],
  loading = false,
  error = null,
  onSelectJob,
  onTriggerMatch,
  onNavigate,
}) => {
  const [filterStatus, setFilterStatus] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  if (loading) return <LoadingState message="Fetching active job postings..." rows={5} />;
  if (error) return <ErrorState message={error} />;

  const filteredJobs = jobs.filter((j) => {
    const matchesStatus = filterStatus === "all" || j.status === filterStatus;
    const matchesSearch =
      !searchTerm ||
      j.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      j.company_name?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="page-jobs">
      <div className="page-header-row">
        <div>
          <h2 className="page-title">Job Descriptions</h2>
          <p className="page-subtitle">
            Manage requirements, trigger multi-candidate rankings, and review AI decompositions.
          </p>
        </div>
        <button
          onClick={() => onNavigate("create-job")}
          className="btn-primary"
        >
          <PlusCircle size={16} className="icon-mr" /> Create Job Description
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="filter-bar">
        <div className="search-input-wrapper">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search by title, department, or company..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="filter-search-input"
          />
        </div>

        <div className="filter-pills-row">
          <span className="filter-label"><Filter size={13} className="icon-mr" /> Status:</span>
          {["all", "open", "in_progress", "closed"].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`pill-btn ${filterStatus === st ? "active" : ""}`}
            >
              {st.replace("_", " ").toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Jobs Grid */}
      <div className="jobs-list-grid">
        {filteredJobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            onSelect={(id) => onSelectJob(id)}
            onTriggerMatch={(id) => onTriggerMatch(id)}
          />
        ))}

        {filteredJobs.length === 0 && (
          <div className="empty-state-card">
            <h3>No job postings match your filters</h3>
            <p>Try clearing your search term or status filters.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Jobs;
