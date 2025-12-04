/**
 * CMS Page Entry Point
 * Mounts the CMS React component
 */

import React from "react";
import ReactDOM from "react-dom";
import { CMS } from "@js/invenio_app_rdm/pages/administration/cms";

// Wait for DOM to be ready
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("cms-root");

  if (container) {
    // Mount React component
    ReactDOM.render(<CMS apiEndpoint="/api/cms" />, container);
  }
});
