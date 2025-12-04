/**
 * Summary Cards Component
 * Displays key statistics in card format
 */

import React from "react";
import PropTypes from "prop-types";

export const SummaryCards = ({ data }) => {
  const cards = [
    {
      icon: "📚",
      value: data.total_records?.toLocaleString() || "-",
      label: "Total Records",
    },
    {
      icon: "⬇️",
      value: data.total_downloads?.toLocaleString() || "-",
      label: "Total Downloads",
    },
    {
      icon: "👥",
      value: data.active_users?.toLocaleString() || "-",
      label: "Active Users",
    },
    {
      icon: "📈",
      value: data.growth_rate ? `${data.growth_rate}%` : "-",
      label: "Growth Rate",
    },
  ];

  return (
    <div className="stats-grid">
      {cards.map((card, index) => (
        <div key={index} className="stat-card">
          <span className="stat-icon">{card.icon}</span>
          <div className="stat-value">{card.value}</div>
          <div className="stat-label">{card.label}</div>
        </div>
      ))}
    </div>
  );
};

SummaryCards.propTypes = {
  data: PropTypes.shape({
    total_records: PropTypes.number,
    total_downloads: PropTypes.number,
    active_users: PropTypes.number,
    growth_rate: PropTypes.number,
  }).isRequired,
};
