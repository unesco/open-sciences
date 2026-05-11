/**
 * Open Science Dashboards Page Component
 * Three tabs:
 *   1. Global overview  – Leaflet world map with participation data
 *   2. Comparison       – Topic list + donut charts via Chart.js
 *   3. Challenges       – Word cloud / tag-cloud
 */

import React, { useState } from "react";
import { GlobalOverview, Comparison, Challenges, CountryDetail } from "./components";
import { DisclaimerModal } from "./components/DisclaimerModal";
import { TABS } from "./constants";

// ─── Root component ────────────────────────────────────────────────────────

export const Dashboard = () => {
  const [activeTab, setActiveTab] = useState("global");
  // Country detail view: { iso3, name } or null
  const [selectedCountry, setSelectedCountry] = useState(null);
  // Show disclaimer modal on first load
  const [showDisclaimer, setShowDisclaimer] = useState(true);

  const handleCountryClick = (iso3, name) => {
    setSelectedCountry({ iso3, name });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleBackFromCountry = () => {
    setSelectedCountry(null);
  };

  // If a country is selected, show the detail page instead of the dashboard
  if (selectedCountry) {
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
              onClick={() => {
                setSelectedCountry(null);
                setActiveTab(tab.id);
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <CountryDetail
          iso3={selectedCountry.iso3}
          countryName={selectedCountry.name}
          onBack={handleBackFromCountry}
        />
      </div>
    );
  }

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
        {activeTab === "global" && <GlobalOverview onCountryClick={handleCountryClick} />}
        {activeTab === "comparison" && <Comparison onCountryClick={handleCountryClick} />}
        {activeTab === "challenges" && <>Challenges Section</>}
      </div>

      {showDisclaimer && <DisclaimerModal onClose={() => setShowDisclaimer(false)} />}
    </div>
  );
};
