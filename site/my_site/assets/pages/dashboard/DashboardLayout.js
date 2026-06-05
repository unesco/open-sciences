/**
 * DashboardLayout
 * Tab bar + React Router <Routes> for the dashboard SPA.
 */

import React, { useState } from "react";
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { GlobalOverview, Comparison, Challenges } from "./components";
import { DisclaimerModal } from "./components/DisclaimerModal";
import { CountryDetailRoute } from "./CountryDetailRoute";
import { TABS } from "./constants";

export const DashboardLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [showDisclaimer, setShowDisclaimer] = useState(true);

  // Derive the active tab from the current path segment
  const pathSegment = location.pathname.split("/").filter(Boolean)[0] || "global";
  const activeTab = TABS.find((t) => t.id === pathSegment) ? pathSegment : "global";

  const handleTabClick = (tabId) => {
    navigate(`/${tabId}`);
  };

  const handleCountryClick = (iso3, name) => {
    navigate(`/country/${iso3}`, { state: { countryName: name } });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Open Science dashboards</h1>
        <p className="dashboard-description">
          Interactive dashboards tracking implementation of UNESCO
          Recommendation on Open Science by Member States who reported their
          progress to UNESCO. See more details on{" "}
          <a href="/page#about">About page</a>.
        </p>
      </div>

      <div className="dashboard-tabs-bar">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`dashboard-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => handleTabClick(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="dashboard-tab-content">
        <Routes>
          <Route index element={<Navigate to="/global" replace />} />
          <Route path="/global" element={<GlobalOverview onCountryClick={handleCountryClick} />} />
          <Route path="/comparison" element={<Comparison onCountryClick={handleCountryClick} />} />
          <Route path="/challenges" element={<Challenges onCountryClick={handleCountryClick} />} />
          <Route
            path="/country/:iso3"
            element={<CountryDetailRoute onBack={() => navigate(-1)} />}
          />
          <Route path="*" element={<Navigate to="/global" replace />} />
        </Routes>
      </div>

      {showDisclaimer && <DisclaimerModal onClose={() => setShowDisclaimer(false)} />}
    </div>
  );
};
