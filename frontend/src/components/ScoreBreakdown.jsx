import React from "react";
import { CheckCircle2, Shield, Percent, Info } from "lucide-react";

export const ScoreBreakdown = ({ scoreData, finalScore }) => {
  if (!scoreData) return null;

  const score = finalScore ?? scoreData.final_score ?? 0;
  const confidence = scoreData.confidence ? Math.round(scoreData.confidence * 100) : 85;
  const coverage = scoreData.evidence_coverage ? Math.round(scoreData.evidence_coverage * 100) : 80;

  const components = [
    {
      name: "Required Skills",
      weight: "40%",
      score: scoreData.required_skill_score ?? 0,
      color: "#3b82f6",
    },
    {
      name: "Relevant Experience",
      weight: "25%",
      score: scoreData.experience_score ?? 0,
      color: "#8b5cf6",
    },
    {
      name: "Practical Projects",
      weight: "20%",
      score: scoreData.project_score ?? 0,
      color: "#10b981",
    },
    {
      name: "Education & Credentials",
      weight: "10%",
      score: scoreData.education_score ?? 0,
      color: "#f59e0b",
    },
    {
      name: "Additional Skills",
      weight: "5%",
      score: scoreData.additional_skill_score ?? 0,
      color: "#06b6d4",
    },
  ];

  return (
    <div className="score-breakdown-card">
      <div className="score-hero-section">
        <div className="score-radial-box">
          <div className="score-number">{score}</div>
          <div className="score-scale">/ 100</div>
          <div className="score-label">Deterministic Score</div>
        </div>

        <div className="score-calibrations">
          <div className="calibration-badge">
            <Shield size={16} className="badge-icon text-blue" />
            <div>
              <span className="calib-val">{confidence}%</span>
              <span className="calib-lbl">Match Confidence</span>
            </div>
          </div>

          <div className="calibration-badge">
            <Percent size={16} className="badge-icon text-emerald" />
            <div>
              <span className="calib-val">{coverage}%</span>
              <span className="calib-lbl">Evidence Coverage</span>
            </div>
          </div>
        </div>
      </div>

      <div className="components-breakdown-list">
        <h5 className="breakdown-subtitle">Deterministic Weighted Factors</h5>
        {components.map((item, idx) => (
          <div key={idx} className="factor-row">
            <div className="factor-info">
              <span className="factor-name">{item.name}</span>
              <span className="factor-weight">Weight: {item.weight}</span>
            </div>
            <div className="factor-bar-wrapper">
              <div
                className="factor-bar-fill"
                style={{
                  width: `${Math.min(Math.max(item.score, 0), 100)}%`,
                  backgroundColor: item.color,
                }}
              />
            </div>
            <span className="factor-score-val">{item.score} / 100</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ScoreBreakdown;
