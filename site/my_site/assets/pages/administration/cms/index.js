/**
 * CMS Page Component
 * Administration interface for content management
 */

import React from "react";
import PropTypes from "prop-types";

export const CMS = ({ apiEndpoint = "/api/cms" }) => {
  return (
    <div className="cms-page">
      <div className="cms-header">
        <h1>📝 Content Management System</h1>
        <p>Manage pages, content, and site structure</p>
      </div>

      <div className="cms-content">
        <p>CMS interface coming soon...</p>
      </div>
    </div>
  );
};

CMS.propTypes = {
  apiEndpoint: PropTypes.string,
};
