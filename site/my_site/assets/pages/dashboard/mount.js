/**
 * React Dashboard Entry Point
 * Mounts the Dashboard React component with client-side routing
 */

import React from "react";
import ReactDOM from "react-dom";
import { BrowserRouter } from "react-router-dom";
import { Dashboard } from "./index";

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("dashboard-root");
  if (container) {
    ReactDOM.render(
      <BrowserRouter basename="/dashboards">
        <Dashboard />
      </BrowserRouter>,
      container
    );
  }
});
