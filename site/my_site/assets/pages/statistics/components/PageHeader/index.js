/**
 * Page Header Component
 * Displays the page title, description, and test banner
 */

import React from "react";
import PropTypes from "prop-types";

export const PageHeader = ({ showTestBanner = false }) => {
  return (
    <>
      {showTestBanner && (
        <div className="test-banner">
          <div className="test-banner-icon">⚠️</div>
          <div className="test-banner-content">
            <h3>Test Page - Mock Data</h3>
            <p>
              This is a demonstration page. All statistics shown are simulated
              and do not represent real data.
            </p>
          </div>
        </div>
      )}

      <div className="stats-header">
        <h1>📊 UNESCO Science Portal Statistics</h1>
        <p>Real-time analytics and insights into research activities</p>
      </div>
    </>
  );
};

PageHeader.propTypes = {
  showTestBanner: PropTypes.bool,
};
