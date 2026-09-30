import React from "react";
import { Briefcase, Users, GitCompare, Award, PlusCircle, ArrowRight } from "lucide-react";
import StatCard from "../components/StatCard";
import JobCard from "../components/JobCard";
import CandidateCard from "../components/CandidateCard";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";

export const Dashboard = ({
  jobs = [],
  candidates = [],
  loading = false,
  error = null,
  onNavigate,
  onSelectJob,
  onSelectCandidate,
  onTriggerMatch,
}) => {
  if (loading) return <LoadingState message="Loading recruiter dashboard..." rows={4} />;
  if (error) return <ErrorState message={error} />;

  const activeJobs = jobs.filter((j) => j.status !== "closed");
  const totalReqs = jobs.reduce((acc, j) => acc + (j.requirements?.length || 0), 0);

  return (
    <div className="page-dashboard">
      {/* Metrics Row */}
      <div className="stats-grid">
        <StatCard
          title="Active Job Postings"
          value={activeJobs.length}
          subtitle="Decomposed & vector-indexed"
          icon={Briefcase}
          trend={{ positive: true, label: "Active roles" }}
          color="blue"
        />
        <StatCard
          title="Candidate Profiles"
          value={candidates.length}
          subtitle="Extracted with section citations"
          icon={Users}
          trend={{ positive: true, label: "Talent pool" }}
          color="purple"
        />
        <StatCard
          title="Atomic Requirements"
          value={totalReqs}
          subtitle="SkillGraph normalized"
          icon={Award}
          color="emerald"
        />
        <StatCard
          title="Pipeline Engine"
          value="LangGraph"
          subtitle="pgvector + FTS RRF"
          icon={GitCompare}
          color="cyan"
        />
      </div>

      {/* Main Dashboard Layout */}
      <div className="dashboard-columns">
        {/* Left Column: Recent Jobs */}
        <div className="dashboard-section">
          <div className="section-header-row">
            <div>
              <h3 className="section-title">Active Job Descriptions</h3>
              <p className="section-subtitle">Requirements decomposed into atomic vector chunks</p>
            </div>
            <button
              onClick={() => onNavigate("jobs")}
              className="btn-link"
            >
              View All ({jobs.length}) <ArrowRight size={14} className="icon-ml" />
            </button>
          </div>

          <div className="jobs-cards-grid">
            {jobs.slice(0, 4).map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onSelect={(id) => onSelectJob(id)}
                onTriggerMatch={(id) => onTriggerMatch(id)}
              />
            ))}
            {jobs.length === 0 && (
              <div className="empty-panel">
                <p>No job postings yet. Create your first job description to start matching.</p>
                <button
                  onClick={() => onNavigate("create-job")}
                  className="btn-primary btn-sm"
                >
                  <PlusCircle size={14} className="icon-mr" /> Create Job Description
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Candidate Talent Pool */}
        <div className="dashboard-section">
          <div className="section-header-row">
            <div>
              <h3 className="section-title">Candidate Intelligence Pool</h3>
              <p className="section-subtitle">Profiles with grounded citations and skill maps</p>
            </div>
            <button
              onClick={() => onNavigate("candidates")}
              className="btn-link"
            >
              Browse All ({candidates.length}) <ArrowRight size={14} className="icon-ml" />
            </button>
          </div>

          <div className="candidate-cards-list">
            {candidates.slice(0, 4).map((candidate) => (
              <CandidateCard
                key={candidate.id}
                candidate={candidate}
                onSelect={(id) => onSelectCandidate(id)}
              />
            ))}
            {candidates.length === 0 && (
              <div className="empty-panel">
                <p>No candidates in pool yet. Upload resumes to populate candidate intelligence.</p>
                <button
                  onClick={() => onNavigate("candidates")}
                  className="btn-primary btn-sm"
                >
                  Upload Resumes
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
