/**
 * Open Science Dashboards Page Component
 * Three tabs:
 *   1. Global overview  – Leaflet world map with participation data
 *   2. Comparison       – Topic list + donut charts via Chart.js
 *   3. Challenges       – Word cloud / tag-cloud
 */

import React, { useState } from "react";
import { GlobalOverview, Comparison, Challenges } from "./components";

// ─── Constants ─────────────────────────────────────────────────────────────

const TABS = [
  { id: "global", label: "Global overview" },
  { id: "comparison", label: "Comparison across countries & regions" },
  { id: "challenges", label: "Open Science challenges" },
];

// ─── Root component ────────────────────────────────────────────────────────

export const Dashboard = () => {
  const [activeTab, setActiveTab] = useState("global");

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Open Science dashboards</h1>
        <p className="dashboard-description">
          Interactive dashboards tracking implementation of UNESCO
          Recommendation on Open Science by Member States who reported their
          progress to UNESCO. See more details on{" "}
          <a href="/about">About page</a>.
        </p>
      </div>

      <div className="dashboard-tabs-bar">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`dashboard-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="dashboard-tab-content">
        {activeTab === "global" && <>Global Overview Section</>}
        {activeTab === "comparison" && <Comparison />}
        {activeTab === "challenges" && <>Challenges Section</>}
      </div>
    </div>
  );
};
