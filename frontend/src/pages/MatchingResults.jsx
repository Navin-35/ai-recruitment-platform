import React, { useState, useEffect } from "react";
import { ArrowLeft, Sparkles, Award, FileCheck, CheckCircle, RefreshCw, Loader2 } from "lucide-react";
import { matchCandidateToJob } from "../services/matches";
import ScoreBreakdown from "../components/ScoreBreakdown";
import SkillGapPanel from "../components/SkillGapPanel";
import EvidencePanel from "../components/EvidencePanel";
import SkillMatch from "../components/SkillMatch";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";

export const MatchingResults = ({
  jobId,
  candidateId,
  onNavigateBack,
}) => {
  const [matchReport, setMatchReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMatchReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await matchCandidateToJob(jobId, candidateId);
      setMatchReport(data);
    } catch (err) {
      setError(err.message || "Failed to generate candidate matching report.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (jobId && candidateId) {
      fetchMatchReport();
    }
  }, [jobId, candidateId]);

  if (loading) return <LoadingState message="Running LangGraph multi-stage matching pipeline..." rows={5} />;
  if (error) return <ErrorState message={error} onRetry={fetchMatchReport} />;
  if (!matchReport) return <ErrorState message="No match data returned." onRetry={fetchMatchReport} />;

  const explanation = matchReport.grounded_explanation || {};
  const scoreBreakdown = matchReport.score_breakdown || {};
  const skillGaps = matchReport.skill_gaps || {};
  const citations = matchReport.top_evidence_citations || [];

  return (
    <div className="page-matching-results">
      <div className="details-header-nav">
        <button onClick={onNavigateBack} className="btn-secondary btn-sm">
          <ArrowLeft size={14} className="icon-mr" /> Back
        </button>
        <button onClick={fetchMatchReport} className="btn-secondary btn-sm">
          <RefreshCw size={14} className="icon-mr" /> Re-Evaluate Match
        </button>
      </div>

      {/* Hero Match Report Header */}
      <div className="match-report-hero">
        <div className="report-hero-left">
          <span className="pipeline-pill">
            <Sparkles size={13} className="icon-mr" /> LangGraph Orchestrated
          </span>
          <h2 className="report-candidate-name">{matchReport.candidate_name}</h2>
          <p className="report-job-title">Evaluation against: <strong>{matchReport.job_title}</strong></p>
        </div>
        <div className="report-hero-right">
          <div className="final-score-badge">
            <span className="badge-score-val">{matchReport.final_score}</span>
            <span className="badge-score-lbl">Overall Score</span>
          </div>
        </div>
      </div>

      {/* AI Grounded Summary */}
      {explanation.summary && (
        <div className="explanation-card">
          <h4 className="card-heading text-primary">
            <Sparkles size={16} className="icon-mr" /> Executive Match Synthesis
          </h4>
          <p className="explanation-summary-text">{explanation.summary}</p>
          
          <div className="explanation-grid">
            {explanation.key_strengths && explanation.key_strengths.length > 0 && (
              <div className="exp-column exp-strengths">
                <h5>Key Candidate Strengths</h5>
                <ul>
                  {explanation.key_strengths.map((s, idx) => (
                    <li key={idx}>
                      <CheckCircle size={14} className="text-emerald icon-mr" /> {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {explanation.key_concerns && explanation.key_concerns.length > 0 && (
              <div className="exp-column exp-concerns">
                <h5>Evaluation Concerns & Risk Factors</h5>
                <ul>
                  {explanation.key_concerns.map((c, idx) => (
                    <li key={idx}>
                      <span className="text-rose icon-mr">•</span> {c}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Score Breakdown Section */}
      <div className="report-section-block">
        <ScoreBreakdown
          scoreData={scoreBreakdown}
          finalScore={matchReport.final_score}
        />
      </div>

      {/* Two Column Intelligence: Skill Gaps & Evidence */}
      <div className="report-dual-grid">
        <div className="report-grid-col">
          <SkillGapPanel gapAnalysis={skillGaps} />
        </div>
        <div className="report-grid-col">
          <EvidencePanel citations={citations} />
        </div>
      </div>

      {/* Requirement Details Matrix */}
      {scoreBreakdown.requirement_match_details && (
        <div className="report-section-block">
          <SkillMatch details={scoreBreakdown.requirement_match_details} />
        </div>
      )}
    </div>
  );
};

export default MatchingResults;
