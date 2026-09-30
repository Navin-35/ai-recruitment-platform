import React from "react";

export const StatCard = ({ title, value, subtitle, icon: Icon, trend = null, color = "primary" }) => {
  return (
    <div className={`stat-card stat-${color}`}>
      <div className="stat-card-header">
        <span className="stat-card-title">{title}</span>
        {Icon && (
          <div className="stat-card-icon-wrapper">
            <Icon size={20} />
          </div>
        )}
      </div>
      <div className="stat-card-body">
        <h3 className="stat-card-value">{value}</h3>
        {subtitle && <p className="stat-card-subtitle">{subtitle}</p>}
      </div>
      {trend && (
        <div className={`stat-card-trend ${trend.positive ? "trend-up" : "trend-down"}`}>
          <span>{trend.positive ? "↑" : "↓"} {trend.label}</span>
        </div>
      )}
    </div>
  );
};

export default StatCard;
