/**
 * React Dashboard Entry Point
 * Mounts the Dashboard React component
 */

import React from "react";
import ReactDOM from "react-dom";
import { Dashboard } from "./index";

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("dashboard-root");
  if (container) {
    ReactDOM.render(<Dashboard />, container);
  }
});
