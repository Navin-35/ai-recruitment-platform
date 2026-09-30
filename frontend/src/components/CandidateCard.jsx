import React from "react";
import { Mail, Phone, Award, ArrowRight } from "lucide-react";

export const CandidateCard = ({ candidate, onSelect }) => {
  const skillsList = candidate.skills ? candidate.skills.split(",").map((s) => s.strip ? s.strip() : s.trim()).filter(Boolean) : [];

  return (
    <div className="candidate-card" onClick={() => onSelect(candidate.id)}>
      <div className="candidate-card-header">
        <div className="candidate-avatar">
          {candidate.name ? candidate.name.slice(0, 2).toUpperCase() : "CD"}
        </div>
        <div className="candidate-info">
          <h4 className="candidate-name">{candidate.name || "Unnamed Candidate"}</h4>
          <div className="candidate-contacts">
            {candidate.email && (
              <span className="contact-item">
                <Mail size={12} /> {candidate.email}
              </span>
            )}
            {candidate.phone && (
              <span className="contact-item">
                <Phone size={12} /> {candidate.phone}
              </span>
            )}
          </div>
        </div>
      </div>

      {candidate.experience && (
        <p className="candidate-experience-preview">
          {candidate.experience.slice(0, 110)}...
        </p>
      )}

      <div className="candidate-skills-cloud">
        {skillsList.slice(0, 5).map((skill, idx) => (
          <span key={idx} className="badge-skill">
            {skill}
          </span>
        ))}
        {skillsList.length > 5 && (
          <span className="badge-more">+{skillsList.length - 5}</span>
        )}
      </div>

      <div className="candidate-card-footer">
        <span className="view-profile-text">View Full Profile</span>
        <ArrowRight size={14} />
      </div>
    </div>
  );
};

export default CandidateCard;
