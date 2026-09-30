import React from "react";
import { Quote, FileText, CheckCircle, ExternalLink } from "lucide-react";

export const EvidencePanel = ({ citations = [] }) => {
  if (!citations || citations.length === 0) {
    return (
      <div className="evidence-panel">
        <h4 className="card-heading">Grounded Document Evidence</h4>
        <p className="no-evidence-text">
          No document citations indexed yet. Run the matching pipeline to extract grounded quotes from the candidate's resume.
        </p>
      </div>
    );
  }

  return (
    <div className="evidence-panel">
      <div className="evidence-header">
        <h4 className="card-heading">Grounded Evidence Citations</h4>
        <span className="evidence-count-badge">
          {citations.length} Grounded Source Snippets
        </span>
      </div>

      <div className="citations-list">
        {citations.map((item, idx) => {
          const strength = item.evidence_strength
            ? Math.round(item.evidence_strength * 100)
            : 75;
          const page = item.page_number || 1;
          const section = item.section || "experience";

          return (
            <div key={idx} className="citation-card">
              <div className="citation-top">
                <div className="citation-badges">
                  <span className={`citation-section-badge section-${section}`}>
                    {section.toUpperCase()}
                  </span>
                  <span className="citation-page-badge">
                    <FileText size={12} className="icon-mr" /> Page {page}
                  </span>
                </div>
                <div className="citation-strength">
                  <span className="strength-label">Cross-Encoder: </span>
                  <span className="strength-val">{strength}% Relevance</span>
                </div>
              </div>

              <div className="citation-body">
                <Quote size={16} className="quote-icon" />
                <p className="citation-quote">
                  "{item.citation_quote || item.content?.slice(0, 160)}..."
                </p>
              </div>

              {item.content && (
                <details className="citation-full-snippet">
                  <summary>View Contextual Chunk</summary>
                  <p className="chunk-content-text">{item.content}</p>
                </details>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EvidencePanel;
