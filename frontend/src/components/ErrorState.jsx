import React from "react";
import { RefreshCw, AlertCircle } from "lucide-react";

export const ErrorState = ({ message = "Something went wrong.", onRetry = null }) => {
  return (
    <div className="error-card">
      <div className="error-content">
        <div className="error-icon-box">
          <AlertCircle size={20} />
        </div>
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

export default ErrorState;
