import React, { useState, useEffect } from "react";
import { ArrowLeft, Mail, Phone, Award, Briefcase, GraduationCap, FileText, Download } from "lucide-react";
import { useCandidate } from "../hooks/useCandidates";
import { getResumesByCandidate, getResumeSignedUrl } from "../services/resumes";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";

export const CandidateDetails = ({ candidateId, onNavigateBack, onMatchAgainstJob = null }) => {
  const { candidate, loading, error, refetch } = useCandidate(candidateId);
  const [resumes, setResumes] = useState([]);
  const [loadingResumes, setLoadingResumes] = useState(false);

  useEffect(() => {
    if (candidateId) {
      setLoadingResumes(true);
      getResumesByCandidate(candidateId)
        .then((data) => setResumes(data))
        .catch((err) => console.error("Could not fetch resumes:", err))
        .finally(() => setLoadingResumes(false));
    }
  }, [candidateId]);

  if (loading) return <LoadingState message="Loading candidate profile..." />;
  if (error || !candidate) return <ErrorState message={error || "Candidate not found"} onRetry={refetch} />;

  const skills = candidate.skills ? candidate.skills.split(",").map((s) => s.trim()).filter(Boolean) : [];

  const handleDownloadSigned = async (resumeId) => {
    try {
      const data = await getResumeSignedUrl(resumeId);
      if (data.signed_url) {
        window.open(data.signed_url, "_blank");
      }
    } catch (err) {
      alert("Signed URL error: " + err.message);
    }
  };

  return (
    <div className="page-candidate-details">
      <div className="details-header-nav">
        <button onClick={onNavigateBack} className="btn-secondary btn-sm">
          <ArrowLeft size={14} className="icon-mr" /> Back to Candidates
        </button>
      </div>

      {/* Candidate Profile Header Card */}
      <div className="candidate-profile-hero">
        <div className="profile-hero-left">
          <div className="profile-large-avatar">
            {candidate.name ? candidate.name.slice(0, 2).toUpperCase() : "CD"}
          </div>
          <div>
            <h2 className="profile-name">{candidate.name || "Candidate #" + candidate.id}</h2>
            <div className="profile-contact-row">
              {candidate.email && (
                <span className="contact-pill"><Mail size={13} /> {candidate.email}</span>
              )}
              {candidate.phone && (
                <span className="contact-pill"><Phone size={13} /> {candidate.phone}</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Skills Matrix Cloud */}
      <div className="profile-section-card">
        <h4 className="section-title">
          <Award size={16} className="icon-mr" /> Verified & Extracted Competencies ({skills.length})
        </h4>
        <div className="skills-badge-wrap">
          {skills.map((s, i) => (
            <span key={i} className="skill-chip-large">
              {s}
            </span>
          ))}
          {skills.length === 0 && <p className="text-muted">No skills parsed yet.</p>}
        </div>
      </div>

      {/* Experience & Projects Grid */}
      <div className="profile-two-columns">
        <div className="profile-section-card">
          <h4 className="section-title">
            <Briefcase size={16} className="icon-mr" /> Work History & Experience
          </h4>
          <div className="profile-text-content">
            {candidate.experience ? (
              <pre className="pre-formatted-text">{candidate.experience}</pre>
            ) : (
              <p className="text-muted">No work experience entries recorded.</p>
            )}
          </div>
        </div>

        <div className="profile-section-card">
          <h4 className="section-title">
            <GraduationCap size={16} className="icon-mr" /> Projects & Education
          </h4>
          <div className="profile-text-content">
            {candidate.projects && (
              <div className="sub-block">
                <h5>Projects</h5>
                <pre className="pre-formatted-text">{candidate.projects}</pre>
              </div>
            )}
            {candidate.education && (
              <div className="sub-block">
                <h5>Education</h5>
                <pre className="pre-formatted-text">{candidate.education}</pre>
              </div>
            )}
            {!candidate.projects && !candidate.education && (
              <p className="text-muted">No project or education records found.</p>
            )}
          </div>
        </div>
      </div>

      {/* Uploaded Documents List */}
      <div className="profile-section-card">
        <h4 className="section-title">
          <FileText size={16} className="icon-mr" /> Uploaded Resume Documents ({resumes.length})
        </h4>
        <div className="resumes-files-list">
          {resumes.map((r) => (
            <div key={r.id} className="resume-file-item">
              <div className="resume-file-info">
                <FileText size={20} className="text-blue" />
                <div>
                  <span className="file-name">{r.filename}</span>
                  <span className="file-status">Status: {r.processing_status}</span>
                </div>
              </div>
              <button
                onClick={() => handleDownloadSigned(r.id)}
                className="btn-secondary btn-sm"
              >
                <Download size={13} className="icon-mr" /> Preview / Download
              </button>
            </div>
          ))}
          {resumes.length === 0 && !loadingResumes && (
            <p className="text-muted">No source files stored for this candidate.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default CandidateDetails;
