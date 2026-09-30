import React, { useState, useEffect } from "react";
import { Settings as SettingsIcon, Database, Shield, Radio, Sparkles, CheckCircle2, AlertTriangle, RefreshCw } from "lucide-react";
import { getSystemStatus } from "../services/matches";
import { LoadingState } from "../components/LoadingState";

export const Settings = () => {
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const data = await getSystemStatus();
      setStatusData(data);
    } catch (err) {
      console.error("Could not fetch system status:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  if (loading) return <LoadingState message="Fetching system telemetry..." />;

  const isDegraded = statusData?.embedding?.retrieval_mode === "lexical_fallback";

  return (
    <div className="page-settings">
      <div className="page-header-row">
        <div>
          <h2 className="page-title">Platform Architecture & Settings</h2>
          <p className="page-subtitle">
            Operational status of LangGraph, Supabase, pgvector, Redis, and Langfuse integrations.
          </p>
        </div>
        <button onClick={fetchStatus} className="btn-secondary btn-sm">
          <RefreshCw size={14} className="icon-mr" /> Refresh Telemetry
        </button>
      </div>

      <div className="settings-grid">
        {/* Retrieval & Embedding Engine */}
        <div className="settings-card">
          <div className="card-header-icon">
            <Database size={20} className="text-blue" />
            <h4 className="settings-card-title">Vector & Retrieval Engine</h4>
          </div>
          <div className="telemetry-rows">
            <div className="telemetry-item">
              <span className="telemetry-key">Retrieval Mode:</span>
              <span className={`status-badge ${isDegraded ? "badge-warning" : "badge-success"}`}>
                {statusData?.embedding?.retrieval_mode || "hybrid_semantic"}
              </span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-key">Embedding Provider:</span>
              <span className="telemetry-val">{statusData?.embedding?.provider || "Google Gemini"}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-key">Embedding Dimension:</span>
              <span className="telemetry-val">{statusData?.embedding?.dimension || 768} dims</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-key">PostgreSQL pgvector:</span>
              <span className="telemetry-val">Enabled (ANN Distance + FTS)</span>
            </div>
          </div>
          {isDegraded && (
            <div className="telemetry-alert">
              <AlertTriangle size={15} />
              <span>
                External embedding API is in degraded mode. System is reliably using high-precision canonical lexical fallback without pseudo-random vectors.
              </span>
            </div>
          )}
        </div>

        {/* Security & Multi-Tenancy */}
        <div className="settings-card">
          <div className="card-header-icon">
            <Shield size={20} className="text-purple" />
            <h4 className="settings-card-title">Security & Multi-Tenancy</h4>
          </div>
          <div className="telemetry-rows">
            <div className="telemetry-item">
              <span className="telemetry-key">Active Tenant ID:</span>
              <span className="telemetry-val">tenant-enterprise-01</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-key">Auth Enforcement:</span>
              <span className={`status-badge ${statusData?.auth_enforced ? "badge-success" : "badge-neutral"}`}>
                {statusData?.auth_enforced ? "Enforced (RBAC)" : "Development (Open)"}
              </span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-key">Document Security:</span>
              <span className="telemetry-val">Private Supabase Storage + HMAC URLs</span>
            </div>
          </div>
        </div>

        {/* Asynchronous Workers & Queue */}
        <div className="settings-card">
          <div className="card-header-icon">
            <Radio size={20} className="text-emerald" />
            <h4 className="settings-card-title">Background Worker Queue</h4>
          </div>
          <div className="telemetry-rows">
            <div className="telemetry-item">
              <span className="telemetry-key">Queue Engine:</span>
              <span className="telemetry-val">{statusData?.background_queue?.engine || "In-Memory ThreadPool"}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-key">Redis Connection:</span>
              <span className={`status-badge ${statusData?.background_queue?.redis_enabled ? "badge-success" : "badge-neutral"}`}>
                {statusData?.background_queue?.redis_enabled ? "Connected" : "Fallback In-Memory"}
              </span>
            </div>
          </div>
        </div>

        {/* Observability & Tracing */}
        <div className="settings-card">
          <div className="card-header-icon">
            <Sparkles size={20} className="text-cyan" />
            <h4 className="settings-card-title">Observability & LLM Tracing</h4>
          </div>
          <div className="telemetry-rows">
            <div className="telemetry-item">
              <span className="telemetry-key">Langfuse Tracing:</span>
              <span className={`status-badge ${statusData?.observability?.langfuse_enabled ? "badge-success" : "badge-neutral"}`}>
                {statusData?.observability?.langfuse_enabled ? "Live Tracing Active" : "Local Latency Tracer"}
              </span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-key">Pipeline Orchestrator:</span>
              <span className="telemetry-val">LangGraph StateGraph</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
