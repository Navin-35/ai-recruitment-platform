import React from "react";
import { Loader2, RefreshCw } from "lucide-react";

export const LoadingState = ({ message = "Loading intelligence...", rows = 3 }) => {
  return (
    <div className="loading-container">
      <div className="spinner-wrapper">
        <Loader2 className="spinner-icon animate-spin" size={32} />
      </div>
      <p className="loading-message">{message}</p>
      <div className="skeleton-group">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="skeleton-bar" style={{ width: `${85 - i * 15}%` }} />
        ))}
      </div>
    </div>
  );
};

export const ErrorState = ({ message = "Something went wrong.", onRetry = null }) => {
  return (
    <div className="error-card">
      <div className="error-content">
        <div className="error-icon-box">!</div>
        <div className="error-text-group">
          <h4 className="error-title">Action Failed</h4>
          <p className="error-description">{message}</p>
        </div>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary retry-btn">
          <RefreshCw size={14} className="icon-mr" /> Retry
        </button>
      )}
    </div>
  );
};
