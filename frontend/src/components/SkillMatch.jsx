import React from "react";
import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react";

export const SkillMatch = ({ matchedSkills = [], details = [] }) => {
  return (
    <div className="skill-match-card">
      <h4 className="card-heading">Requirement Matching Breakdown</h4>
      <div className="skills-grid">
        {details.length > 0
          ? details.map((d, i) => {
              const isMatch = d.score >= 50;
              return (
                <div
                  key={i}
                  className={`skill-match-item ${isMatch ? "matched" : "unmatched"}`}
                >
                  <div className="item-header">
                    <span className="skill-title">{d.skill}</span>
                    {isMatch ? (
                      <CheckCircle2 size={16} className="text-emerald" />
                    ) : (
                      <XCircle size={16} className="text-rose" />
                    )}
                  </div>
                  <div className="item-meta">
                    <span className={`importance-tag imp-${d.importance?.toLowerCase()}`}>
                      {d.importance || "medium"}
                    </span>
                    <span className="score-text">Score: {d.score}%</span>
                  </div>
                </div>
              );
            })
          : matchedSkills.map((m, i) => (
              <div key={i} className="skill-match-item matched">
                <div className="item-header">
                  <span className="skill-title">{m.skill || m}</span>
                  <CheckCircle2 size={16} className="text-emerald" />
                </div>
                <div className="item-meta">
                  <span className="importance-tag imp-high">
                    {m.importance || "Required"}
                  </span>
                  {m.evidence_strength && (
                    <span className="score-text">Strength: {Math.round(m.evidence_strength * 100)}%</span>
                  )}
                </div>
              </div>
            ))}
      </div>
    </div>
  );
};

export default SkillMatch;
