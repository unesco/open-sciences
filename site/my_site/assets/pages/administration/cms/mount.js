/**
 * CMS Page Entry Point
 * Mounts the Resource-Driven CMS React component
 */

import React from "react";
import ReactDOM from "react-dom";
import { ResourceCMS } from "./index";

// Wait for DOM to be ready
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("cms-root");

  if (container) {
    // Mount the Resource-Driven CMS component
    ReactDOM.render(<ResourceCMS apiEndpoint="/data/cms" />, container);
  }
});
