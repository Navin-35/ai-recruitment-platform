import React from "react";
import { Eye, FileCheck, ArrowUpRight } from "lucide-react";

export const CandidateTable = ({ candidates, onSelectCandidate, onMatchCandidate = null }) => {
  if (!candidates || candidates.length === 0) {
    return (
      <div className="empty-table-state">
        <p>No candidates found in pool. Upload resumes to populate candidate intelligence.</p>
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <table className="enterprise-table">
        <thead>
          <tr>
            <th>Candidate</th>
            <th>Contact</th>
            <th>Primary Skills</th>
            <th>Education / Credentials</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c) => {
            const skills = c.skills ? c.skills.split(",").map((s) => s.trim()).filter(Boolean) : [];
            return (
              <tr key={c.id}>
                <td className="table-primary-cell">
                  <div className="cell-avatar-group">
                    <div className="table-avatar">
                      {c.name ? c.name.slice(0, 2).toUpperCase() : "CD"}
                    </div>
                    <div>
                      <div className="cell-main-text">{c.name || "Candidate #" + c.id}</div>
                      <div className="cell-sub-text">ID: #{c.id}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <div className="cell-main-text">{c.email || "—"}</div>
                  <div className="cell-sub-text">{c.phone || ""}</div>
                </td>
                <td>
                  <div className="table-skills-group">
                    {skills.slice(0, 3).map((s, i) => (
                      <span key={i} className="table-skill-chip">{s}</span>
                    ))}
                    {skills.length > 3 && (
                      <span className="table-skill-chip chip-more">+{skills.length - 3}</span>
                    )}
                  </div>
                </td>
                <td>
                  <span className="education-summary">
                    {c.education ? c.education.split("\n")[0].slice(0, 40) : "Not listed"}
                  </span>
                </td>
                <td>
                  <div className="table-actions">
                    <button
                      onClick={() => onSelectCandidate(c.id)}
                      className="btn-table-icon"
                      title="View Profile & Citations"
                    >
                      <Eye size={15} />
                    </button>
                    {onMatchCandidate && (
                      <button
                        onClick={() => onMatchCandidate(c.id)}
                        className="btn-table-action"
                      >
                        Match <ArrowUpRight size={13} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default CandidateTable;
