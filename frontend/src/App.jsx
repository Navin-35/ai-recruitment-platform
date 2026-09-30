import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Jobs from "./pages/Jobs";
import CreateJob from "./pages/CreateJob";
import JobDetails from "./pages/JobDetails";
import Candidates from "./pages/Candidates";
import CandidateDetails from "./pages/CandidateDetails";
import MatchingResults from "./pages/MatchingResults";
import Settings from "./pages/Settings";
import { useJobs } from "./hooks/useJobs";
import { useCandidates } from "./hooks/useCandidates";
import { getSystemStatus } from "./services/matches";
import "./index.css";

export function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [globalSearch, setGlobalSearch] = useState("");

  const { jobs, loading: jobsLoading, error: jobsError, refetch: refetchJobs } = useJobs(globalSearch);
  const { candidates, loading: candidatesLoading, error: candidatesError, refetch: refetchCandidates } = useCandidates(globalSearch);

  useEffect(() => {
    getSystemStatus()
      .then((data) => setSystemStatus(data))
      .catch((err) => console.warn("System telemetry not yet reachable:", err));
  }, []);

  const handleSelectJob = (jobId) => {
    setSelectedJobId(jobId);
    setActiveTab("job-details");
  };

  const handleSelectCandidate = (candidateId) => {
    setSelectedCandidateId(candidateId);
    setActiveTab("candidate-details");
  };

  const handleViewCandidateMatch = (jobId, candidateId) => {
    setSelectedJobId(jobId);
    setSelectedCandidateId(candidateId);
    setActiveTab("matching-results");
  };

  const handleTriggerMatchForJob = (jobId) => {
    setSelectedJobId(jobId);
    // If candidates exist, match against the top one or open job details
    if (candidates && candidates.length > 0) {
      setSelectedCandidateId(candidates[0].id);
      setActiveTab("matching-results");
    } else {
      setSelectedJobId(jobId);
      setActiveTab("job-details");
    }
  };

  return (
    <div className="platform-layout">
      {/* Top Navigation */}
      <Navbar
        systemStatus={systemStatus}
        onSearch={(term) => setGlobalSearch(term)}
        activeTenant="Enterprise HR"
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
      />

      <div className="platform-body">
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={(tab) => {
            setActiveTab(tab);
          }}
        />

        {/* Dynamic Main Workspace Content */}
        <main className="platform-content">
          {activeTab === "dashboard" && (
            <Dashboard
              jobs={jobs}
              candidates={candidates}
              loading={jobsLoading || candidatesLoading}
              error={jobsError || candidatesError}
              onNavigate={(tab) => setActiveTab(tab)}
              onSelectJob={handleSelectJob}
              onSelectCandidate={handleSelectCandidate}
              onTriggerMatch={handleTriggerMatchForJob}
            />
          )}

          {activeTab === "jobs" && (
            <Jobs
              jobs={jobs}
              loading={jobsLoading}
              error={jobsError}
              onSelectJob={handleSelectJob}
              onTriggerMatch={handleTriggerMatchForJob}
              onNavigate={(tab) => setActiveTab(tab)}
            />
          )}

          {activeTab === "create-job" && (
            <CreateJob
              onJobCreated={(job) => {
                refetchJobs();
                handleSelectJob(job.id);
              }}
              onNavigateBack={() => setActiveTab("jobs")}
            />
          )}

          {activeTab === "job-details" && selectedJobId && (
            <JobDetails
              jobId={selectedJobId}
              onNavigateBack={() => setActiveTab("jobs")}
              onViewCandidateMatch={handleViewCandidateMatch}
            />
          )}

          {activeTab === "candidates" && (
            <Candidates
              candidates={candidates}
              loading={candidatesLoading}
              error={candidatesError}
              onSelectCandidate={handleSelectCandidate}
              onCandidateCreated={() => refetchCandidates()}
            />
          )}

          {activeTab === "candidate-details" && selectedCandidateId && (
            <CandidateDetails
              candidateId={selectedCandidateId}
              onNavigateBack={() => setActiveTab("candidates")}
              onMatchAgainstJob={(jobId) => handleViewCandidateMatch(jobId, selectedCandidateId)}
            />
          )}

          {activeTab === "matches" && (
            <div className="page-matches-overview">
              <div className="page-header-row">
                <div>
                  <h2 className="page-title">Candidate Evaluation & Matches</h2>
                  <p className="page-subtitle">
                    Select a job description to inspect candidate rankings and grounded evidence reports.
                  </p>
                </div>
              </div>
              <div className="jobs-list-grid">
                {jobs.map((job) => (
                  <div key={job.id} className="match-job-card" onClick={() => handleSelectJob(job.id)}>
                    <div className="job-title-row">
                      <h4>{job.title}</h4>
                      <span className="badge-pill">{job.company_name || "Enterprise"}</span>
                    </div>
                    <p className="job-desc-preview">{job.description?.slice(0, 110)}...</p>
                    <div className="match-card-action">
                      <span>Inspect Match Leaderboard →</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "matching-results" && selectedJobId && selectedCandidateId && (
            <MatchingResults
              jobId={selectedJobId}
              candidateId={selectedCandidateId}
              onNavigateBack={() => setActiveTab("job-details")}
            />
          )}

          {activeTab === "settings" && <Settings />}
        </main>
      </div>
    </div>
  );
}

export default App;