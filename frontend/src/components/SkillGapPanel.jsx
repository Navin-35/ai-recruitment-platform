import React from "react";
import { AlertTriangle, AlertCircle, Sparkles, BookOpen } from "lucide-react";

export const SkillGapPanel = ({ gapAnalysis }) => {
  if (!gapAnalysis) return null;

  const missingReq = gapAnalysis.missing_required || [];
  const missingOpt = gapAnalysis.missing_optional || [];
  const weakSkills = gapAnalysis.weak_skills || [];

  return (
    <div className="skill-gap-panel">
      <div className="gap-panel-header">
        <h4 className="card-heading">Skill-Gap Analysis & Upskilling Intelligence</h4>
        <div className="coverage-indicator">
          <span>Requirement Coverage: </span>
          <strong>{gapAnalysis.coverage_percentage}%</strong>
        </div>
      </div>

      {/* Critical Missing Mandatory Skills */}
      {missingReq.length > 0 && (
        <div className="gap-section">
          <div className="section-title text-rose">
            <AlertCircle size={16} />
            <span>Missing Mandatory Competencies ({missingReq.length})</span>
          </div>
          <div className="gap-cards-list">
            {missingReq.map((gap, i) => (
              <div key={i} className="gap-card gap-critical">
                <div className="gap-card-top">
                  <span className="gap-skill-name">{gap.skill}</span>
                  <span className={`severity-tag sev-${gap.severity || "high"}`}>
                    {gap.severity || "high"} severity
                  </span>
                </div>
                {gap.recommendation && (
                  <p className="gap-rec">
                    <BookOpen size={12} className="icon-mr" /> {gap.recommendation}
                  </p>
                )}
                {gap.related_skills && gap.related_skills.length > 0 && (
                  <div className="related-skills-tags">
                    <span>Related: </span>
                    {gap.related_skills.map((rel, idx) => (
                      <span key={idx} className="chip-related">{rel}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Weak Skills (Declared but unverified) */}
      {weakSkills.length > 0 && (
        <div className="gap-section">
          <div className="section-title text-amber">
            <AlertTriangle size={16} />
            <span>Weak / Unverified Skills ({weakSkills.length})</span>
          </div>
          <p className="section-hint">
            These skills were declared in the candidate's skills section, but lack practical evidence in work history or project highlights.
          </p>
          <div className="gap-cards-list">
            {weakSkills.map((ws, i) => (
              <div key={i} className="gap-card gap-warning">
                <div className="gap-card-top">
                  <span className="gap-skill-name">{ws.skill}</span>
                  <span className="severity-tag sev-medium">Unverified Claim</span>
                </div>
                <p className="gap-reason">{ws.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing Preferred / Nice to Haves */}
      {missingOpt.length > 0 && (
        <div className="gap-section">
          <div className="section-title text-blue">
            <Sparkles size={16} />
            <span>Preferred & Optional Skill Opportunities ({missingOpt.length})</span>
          </div>
          <div className="gap-chips-group">
            {missingOpt.map((opt, i) => (
              <span key={i} className="chip-optional">
                {opt.skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {missingReq.length === 0 && weakSkills.length === 0 && (
        <div className="no-gaps-state">
          <div className="no-gaps-badge">✓ Complete Skill Alignment</div>
          <p>Candidate satisfies 100% of required technical competencies with verified citations.</p>
        </div>
      )}
    </div>
  );
};

export default SkillGapPanel;
