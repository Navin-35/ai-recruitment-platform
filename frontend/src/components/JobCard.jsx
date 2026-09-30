import React from "react";
import { Building2, MapPin, Sparkles, ChevronRight, CheckCircle2 } from "lucide-react";

export const JobCard = ({ job, onSelect, onTriggerMatch }) => {
  const requirements = job.requirements || [];
  const reqCount = requirements.length;

  return (
    <div className="job-card">
      <div className="job-card-header">
        <div>
          <h4 className="job-card-title">{job.title}</h4>
          <div className="job-card-meta">
            {job.company_name && (
              <span className="meta-item">
                <Building2 size={13} /> {job.company_name}
              </span>
            )}
            {job.location && (
              <span className="meta-item">
                <MapPin size={13} /> {job.location}
              </span>
            )}
          </div>
        </div>
        <span className={`status-pill status-${job.status || "open"}`}>
          {job.status || "open"}
        </span>
      </div>

      <p className="job-card-description">
        {job.description ? `${job.description.slice(0, 130)}...` : "No description provided."}
      </p>

      {reqCount > 0 && (
        <div className="job-card-requirements">
          <div className="requirements-tags-list">
            {requirements.slice(0, 4).map((r, i) => (
              <span key={i} className={`skill-tag ${r.is_required ? "skill-required" : "skill-optional"}`}>
                {r.skill_name}
              </span>
            ))}
            {reqCount > 4 && (
              <span className="skill-tag skill-more">+{reqCount - 4} more</span>
            )}
          </div>
        </div>
      )}

      <div className="job-card-footer">
        <button
          onClick={() => onSelect(job.id)}
          className="btn-secondary btn-sm"
        >
          View Details
        </button>
        <button
          onClick={() => onTriggerMatch(job.id)}
          className="btn-primary btn-sm"
        >
          <Sparkles size={14} className="icon-mr" /> Match Pool
        </button>
      </div>
    </div>
  );
};

export default JobCard;
