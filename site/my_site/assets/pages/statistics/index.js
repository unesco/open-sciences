/**
 * Statistics Page Component
 * Displays summary statistics, charts, and recent activities
 */

import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import {
  PageHeader,
  SummaryCards,
  ActivityChart,
  TopSubjects,
  RecentActivities,
} from "./components";
import { Message } from "semantic-ui-react";

export const Statistics = ({
  apiEndpoint = "/data/statistics",
  showTestBanner = false,
}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(apiEndpoint);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const jsonData = await response.json();
      setData(jsonData);
    } catch (err) {
      console.error("Error loading statistics:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <p>Loading statistics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Message negative>
        <Message.Header>⚠️ Error Loading Statistics</Message.Header>
        <p>Unable to load statistics data: {error}</p>
        <button className="ui button primary" onClick={loadData}>
          🔄 Try Again
        </button>
      </Message>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="statistics-page">
      {/* Page Header */}
      <PageHeader showTestBanner={showTestBanner} />

      {/* Summary Statistics Cards */}
      <SummaryCards data={data.summary} />

      {/* Charts Grid */}
      <div className="charts-grid">
        <ActivityChart data={data.daily_activity} />
        <TopSubjects data={data.top_subjects} />
      </div>

      {/* Recent Activities */}
      <RecentActivities data={data.recent_activities} />

      {/* Footer */}
      <div className="stats-footer">
        <div className="last-update">
          🕐 Last updated: <strong>{data.last_updated}</strong>
        </div>
        <button className="ui button primary" onClick={loadData}>
          🔄 Refresh Data
        </button>
      </div>
    </div>
  );
};

Statistics.propTypes = {
  apiEndpoint: PropTypes.string,
  showTestBanner: PropTypes.bool,
};
