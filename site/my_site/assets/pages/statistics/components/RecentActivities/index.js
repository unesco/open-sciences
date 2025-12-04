/**
 * Recent Activities Component
 * Displays recent activity feed with emoji indicators
 */

import React from "react";
import PropTypes from "prop-types";

export const RecentActivities = ({ data }) => {
  const getEmoji = (action) => {
    if (action.includes("uploaded") || action.includes("caricato")) return "⬆️";
    if (action.includes("downloaded") || action.includes("scaricato"))
      return "⬇️";
    if (action.includes("updated") || action.includes("aggiornato"))
      return "✏️";
    if (action.includes("deleted") || action.includes("eliminato")) return "🗑️";
    if (action.includes("commented") || action.includes("commentato"))
      return "💬";
    if (action.includes("shared") || action.includes("condiviso")) return "🔗";
    return "📄";
  };

  const getTimeAgo = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) return "appena ora";
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min fa`;
    if (diffInSeconds < 86400)
      return `${Math.floor(diffInSeconds / 3600)} ore fa`;
    if (diffInSeconds < 604800)
      return `${Math.floor(diffInSeconds / 86400)} giorni fa`;
    return date.toLocaleDateString("it-IT", { day: "numeric", month: "short" });
  };

  return (
    <div className="chart-card" style={{ marginTop: "24px" }}>
      <div className="chart-title">📋 Recent Activities</div>
      <div>
        {data.map((activity, index) => (
          <div key={index} className="activity-item">
            <div className="activity-icon">{getEmoji(activity.action)}</div>
            <div className="activity-content">
              <div className="activity-action">{activity.action}</div>
              <div className="activity-title" title={activity.title}>
                {activity.title}
              </div>
              <div className="activity-time">{getTimeAgo(activity.time)}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

RecentActivities.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      action: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      time: PropTypes.string.isRequired,
    })
  ).isRequired,
};
