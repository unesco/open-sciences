/**
 * React Statistics Dashboard Entry Point
 * Mounts the StatisticsDashboard React component
 */

import React from "react";
import ReactDOM from "react-dom";
import { Statistics } from "@js/invenio_app_rdm/pages/statistics";

// Wait for DOM to be ready
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("statistics-root");

  if (container) {
    // Mount React component
    ReactDOM.render(
      <Statistics apiEndpoint="/data/statistics" showTestBanner={true} />,
      container
    );
  }
});
