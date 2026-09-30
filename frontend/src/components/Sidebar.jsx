import React from "react";
import { LayoutDashboard, Briefcase, Users, GitCompare, Settings, PlusCircle, FileText } from "lucide-react";

export const Sidebar = ({ activeTab, onSelectTab }) => {
  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "jobs", label: "Job Postings", icon: Briefcase },
    { id: "candidates", label: "Candidate Pool", icon: Users },
    { id: "matches", label: "Matching & Ranking", icon: GitCompare },
    { id: "settings", label: "Platform Settings", icon: Settings },
  ];

  return (
    <aside className="app-sidebar">
      <div className="sidebar-action-card">
        <button
          onClick={() => onSelectTab("create-job")}
          className="btn-primary sidebar-create-btn"
        >
          <PlusCircle size={16} className="btn-icon" />
          <span>New Job Description</span>
        </button>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`sidebar-nav-item ${isActive ? "active" : ""}`}
            >
              <Icon size={18} className="sidebar-nav-icon" />
              <span className="sidebar-nav-label">{item.label}</span>
              {isActive && <div className="active-indicator" />}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="architecture-badge">
          <FileText size={14} />
          <span>LangGraph + Gemini</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
