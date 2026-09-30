import React from "react";
import { Sparkles, Search, ShieldCheck, Database, Bell } from "lucide-react";

export const Navbar = ({
  systemStatus = null,
  onSearch = null,
  activeTenant = "Enterprise HR",
  activeTab = "dashboard",
  onSelectTab = null,
}) => {
  const isDegraded = systemStatus?.embedding?.retrieval_mode === "lexical_fallback";

  return (
    <header className="app-navbar">
      <div className="navbar-brand">
        <div className="navbar-logo-badge">
          <Sparkles size={18} className="logo-sparkle" />
        </div>
        <div className="navbar-brand-titles">
          <span className="navbar-title">AI Recruitment</span>
          <span className="navbar-subtitle">Candidate Matching & Intelligence</span>
        </div>
      </div>

      {onSelectTab && (
        <nav className="navbar-nav-links">
          <button
            type="button"
            className={`nav-tab-btn ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => onSelectTab("dashboard")}
          >
            Dashboard
          </button>
          <button
            type="button"
            className={`nav-tab-btn ${activeTab === "jobs" || activeTab === "job-details" ? "active" : ""}`}
            onClick={() => onSelectTab("jobs")}
          >
            Jobs
          </button>
          <button
            type="button"
            className={`nav-tab-btn ${activeTab === "candidates" || activeTab === "candidate-details" ? "active" : ""}`}
            onClick={() => onSelectTab("candidates")}
          >
            Candidates
          </button>
          <button
            type="button"
            className={`nav-tab-btn ${activeTab === "matches" || activeTab === "matching-results" ? "active" : ""}`}
            onClick={() => onSelectTab("matches")}
          >
            Matches
          </button>
          <button
            type="button"
            className={`nav-tab-btn ${activeTab === "create-job" ? "active" : ""}`}
            onClick={() => onSelectTab("create-job")}
          >
            + Post Job
          </button>
        </nav>
      )}

      <div className="navbar-search-wrapper">
        <Search size={16} className="search-icon" />
        <input
          type="text"
          placeholder="Search jobs, candidates..."
          className="navbar-search-input"
          onChange={(e) => onSearch && onSearch(e.target.value)}
        />
      </div>

      <div className="navbar-actions">
        <div className={`system-status-pill ${isDegraded ? "pill-degraded" : "pill-online"}`}>
          <Database size={13} className="pill-icon" />
          <span className="pill-text">
            {isDegraded ? "Lexical Mode" : "Online"}
          </span>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
