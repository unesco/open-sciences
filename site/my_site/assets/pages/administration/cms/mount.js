/**
 * CMS Page Entry Point
 * Mounts the CMS React component
 */

import React from "react";
import ReactDOM from "react-dom";
import { CMS } from "./index";

// Wait for DOM to be ready
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("cms-root");

  if (container) {
    // Mount React component
    ReactDOM.render(<CMS apiEndpoint="/api/cms" />, container);
  }
});
