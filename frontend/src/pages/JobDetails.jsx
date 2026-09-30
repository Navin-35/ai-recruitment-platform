import React, { useState } from "react";
import { ArrowLeft, Sparkles, Building2, MapPin, CheckCircle, Award, Users, Loader2 } from "lucide-react";
import { useJob } from "../hooks/useJobs";
import { useJobMatches } from "../hooks/useMatches";
import { extractJobRequirements } from "../services/jobs";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";

export const JobDetails = ({
  jobId,
  onNavigateBack,
  onViewCandidateMatch,
}) => {
  const { job, loading, error, refetch } = useJob(jobId);
  const { matches, loading: matchesLoading, ranking, triggerRanking, refetch: refetchMatches } = useJobMatches(jobId);
  const [extracting, setExtracting] = useState(false);

  if (loading) return <LoadingState message="Loading job description intelligence..." />;
  if (error || !job) return <ErrorState message={error || "Job not found"} onRetry={refetch} />;

  const handleExtract = async () => {
    try {
      setExtracting(true);
      await extractJobRequirements(jobId);
      refetch();
    } catch (err) {
      alert("Requirement extraction failed: " + err.message);
    } finally {
      setExtracting(false);
    }
  };

  const requirements = job.requirements || [];

  return (
    <div className="page-job-details">
      <div className="details-header-nav">
        <button onClick={onNavigateBack} className="btn-secondary btn-sm">
          <ArrowLeft size={14} className="icon-mr" /> Back to Jobs
        </button>
        <div className="header-actions-group">
          <button
            onClick={handleExtract}
            disabled={extracting}
            className="btn-secondary btn-sm"
          >
            {extracting ? (
              <Loader2 size={14} className="animate-spin icon-mr" />
            ) : (
              <Award size={14} className="icon-mr" />
            )}
            Re-Extract Atomic Requirements
          </button>
          <button
            onClick={() => triggerRanking()}
            disabled={ranking}
            className="btn-primary btn-sm"
          >
            {ranking ? (
              <Loader2 size={14} className="animate-spin icon-mr" />
            ) : (
              <Sparkles size={14} className="icon-mr" />
            )}
            Run LangGraph Match & Rank
          </button>
        </div>
      </div>

      {/* Hero Card */}
      <div className="job-hero-card">
        <div className="hero-titles">
          <h2 className="job-main-title">{job.title}</h2>
          <div className="job-meta-row">
            {job.company_name && (
              <span className="meta-pill"><Building2 size={14} /> {job.company_name}</span>
            )}
            {job.location && (
              <span className="meta-pill"><MapPin size={14} /> {job.location}</span>
            )}
            <span className={`status-pill status-${job.status}`}>{job.status}</span>
          </div>
        </div>
        <p className="job-full-description">{job.description}</p>
      </div>

      {/* Two Column Section */}
      <div className="job-details-columns">
        {/* Left: Atomic Requirements */}
        <div className="details-section">
          <div className="section-header-compact">
            <h4 className="section-title">
              <Award size={18} className="icon-mr" /> Decomposed Atomic Requirements ({requirements.length})
            </h4>
            <span className="section-caption">Extracted via Gemini & indexed with 768-dim embeddings</span>
          </div>

          <div className="requirements-table-wrapper">
            <table className="enterprise-table compact-table">
              <thead>
                <tr>
                  <th>Competency / Skill</th>
                  <th>Requirement Type</th>
                  <th>Importance</th>
                </tr>
              </thead>
              <tbody>
                {requirements.map((req) => (
                  <tr key={req.id}>
                    <td className="font-semibold text-primary">{req.skill_name}</td>
                    <td>
                      <span className={`badge-pill ${req.is_required ? "badge-required" : "badge-optional"}`}>
                        {req.is_required ? "Mandatory" : "Preferred"}
                      </span>
                    </td>
                    <td>
                      <span className={`importance-tag imp-${req.importance?.toLowerCase()}`}>
                        {req.importance || "medium"}
                      </span>
                    </td>
                  </tr>
                ))}
                {requirements.length === 0 && (
                  <tr>
                    <td colSpan={3} className="empty-table-cell">
                      No atomic requirements extracted yet. Click "Re-Extract Atomic Requirements".
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Candidate Matches Leaderboard */}
        <div className="details-section">
          <div className="section-header-compact">
            <h4 className="section-title">
              <Users size={18} className="icon-mr" /> Candidate Leaderboard ({matches.length})
            </h4>
            <span className="section-caption">Deterministic scoring & grounded evidence</span>
          </div>

          {matchesLoading ? (
            <LoadingState message="Ranking candidate pool..." rows={3} />
          ) : (
            <div className="ranked-candidates-list">
              {matches.map((m, idx) => {
                const rank = idx + 1;
                const score = m.final_score || 0;
                return (
                  <div
                    key={m.match_id || m.candidate_id}
                    className="ranked-match-card"
                    onClick={() => onViewCandidateMatch(job.id, m.candidate_id)}
                  >
                    <div className="rank-badge">#{rank}</div>
                    <div className="candidate-match-info">
                      <div className="cand-match-name">{m.candidate_name || `Candidate #${m.candidate_id}`}</div>
                      <div className="cand-match-sub">
                        {m.matching_skills ? `Matches: ${m.matching_skills.slice(0, 40)}...` : "Matches computed"}
                      </div>
                    </div>
                    <div className="candidate-score-pill">
                      <span className="score-val">{score}</span>
                      <span className="score-denom">/ 100</span>
                    </div>
                  </div>
                );
              })}

              {matches.length === 0 && (
                <div className="empty-panel">
                  <p>No candidates evaluated yet for this role.</p>
                  <button
                    onClick={() => triggerRanking()}
                    className="btn-primary btn-sm"
                  >
                    <Sparkles size={14} className="icon-mr" /> Run Match & Rank
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default JobDetails;
