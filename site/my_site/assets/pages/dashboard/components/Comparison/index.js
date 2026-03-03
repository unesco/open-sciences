/**
 * Comparison Dashboard Component
 * Tab 2: Topic list + donut charts with country breakdown drawer
 */

import React, { useState, useCallback } from "react";
import { DonutChart } from "../DonutChart";
import { CountryBreakdownModal } from "../CountryBreakdownModal";

// ─── Constants ─────────────────────────────────────────────────────────────

const COMPARISON_TOPICS = [
  { id: "t1", label: "Promoting a common understanding of open science, associated benefits, and challenges, as well as diverse paths to open science" },
  { id: "t2", label: "Developing an enabling policy environment for open science" },
  { id: "t3", label: "Investing in open science infrastructures and services" },
  { id: "t4", label: "Investing in human resources, training, education, digital literacy and capacity building for open science" },
  { id: "t5", label: "Fostering a culture of open science and aligning incentives for open science" },
  { id: "t6", label: "Promoting innovative approaches for open science at different stages" },
];

const TOPIC_CHART_DATA = {
  t1: [
    { label: "UNESCO Recommendation on Open Science formally promoted", yes: 55, no: 26, total: 81 },
    { label: "Awareness-raising activities on open science",            yes: 55, no: 26, total: 81 },
  ],
  t2: [
    { label: "National open science policy adopted",  yes: 42, no: 39, total: 81 },
    { label: "Open science action plan in place",     yes: 38, no: 43, total: 81 },
  ],
  t3: [
    { label: "National open access repository operational", yes: 50, no: 31, total: 81 },
    { label: "Open data infrastructure investment",         yes: 45, no: 36, total: 81 },
  ],
  t4: [
    { label: "Open science training programmes available", yes: 47, no: 34, total: 81 },
    { label: "Digital literacy initiatives funded",        yes: 39, no: 42, total: 81 },
  ],
  t5: [
    { label: "Incentives for open publishing",   yes: 33, no: 48, total: 81 },
    { label: "Open science culture promoted",    yes: 52, no: 29, total: 81 },
  ],
  t6: [
    { label: "Citizen science initiatives",   yes: 29, no: 52, total: 81 },
    { label: "Open innovation frameworks",    yes: 36, no: 45, total: 81 },
  ],
};

// ─── MedalIcon sub-component ───────────────────────────────────────────────

const MedalIcon = () => (
  <svg
    className="topic-medal-icon"
    viewBox="0 0 24 24"
    width="20"
    height="20"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="12" cy="14" r="6" fill="#1a6fa8" />
    <circle cx="12" cy="14" r="4" fill="white" />
    <circle cx="12" cy="14" r="2.5" fill="#1a6fa8" />
    <path d="M9 8.5L7 2h10l-2 6.5" stroke="#1a6fa8" strokeWidth="1.5" strokeLinejoin="round" fill="none" />
    <path d="M9 8.5 Q12 10 15 8.5" stroke="#1a6fa8" strokeWidth="1.5" fill="none" />
  </svg>
);

// ─── Comparison component ──────────────────────────────────────────────────

export const Comparison = () => {
  const [selectedTopic, setSelectedTopic] = useState("t1");
  const [showPerRegion, setShowPerRegion] = useState(false);
  const [activeBreakdown, setActiveBreakdown] = useState(null);
  const charts = TOPIC_CHART_DATA[selectedTopic] || [];

  const openBreakdown = useCallback((key, label) => {
    setActiveBreakdown({ key, label });
  }, []);

  const closeBreakdown = useCallback(() => setActiveBreakdown(null), []);

  return (
    <div className="dash-comparison">
      <div className="dashboard-subheader">
        <strong>Select the topic to filter</strong>
        <button type="button" className="dash-btn outline">
          Download ⬇
        </button>
      </div>

      <div className="comparison-main">
        {/* Topic list */}
        <div className="topic-list">
          {COMPARISON_TOPICS.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`topic-card ${selectedTopic === t.id ? "active" : ""}`}
              onClick={() => setSelectedTopic(t.id)}
            >
              <span className="topic-icon">
                <MedalIcon />
              </span>
              <span className="topic-label">{t.label}</span>
              <span className={`topic-radio ${selectedTopic === t.id ? "checked" : ""}`} />
            </button>
          ))}
        </div>

        {/* Donut charts */}
        <div className="comparison-charts">
          <div className="comparison-charts-header">
            <strong>Response Distribution by Question</strong>
          </div>
          <div className="per-region-toggle">
            <label className="toggle-switch" htmlFor="per-region-chk">
              <span className="sr-only">Show per region</span>
              <input
                id="per-region-chk"
                type="checkbox"
                checked={showPerRegion}
                onChange={(e) => setShowPerRegion(e.target.checked)}
              />
              <span className="toggle-slider" />
            </label>
            <span className="toggle-label">Show per region</span>
          </div>
          <div className="donut-grid">
            {charts.map((c, i) => {
              const breakdownKey = `${selectedTopic}-${i}`;
              return (
                <DonutChart
                  key={`${selectedTopic}-${i}`}
                  chartData={c}
                  showPerRegion={showPerRegion}
                  onViewBreakdown={
                    !showPerRegion ? () => openBreakdown(breakdownKey, c.label) : null
                  }
                />
              );
            })}
          </div>
          <p className="donut-footnote">*One response = one Member State</p>
        </div>
      </div>

      {/* Country breakdown modal/drawer */}
      {activeBreakdown && (
        <CountryBreakdownModal
          chartLabel={activeBreakdown.label}
          breakdownKey={activeBreakdown.key}
          onClose={closeBreakdown}
        />
      )}
    </div>
  );
};
