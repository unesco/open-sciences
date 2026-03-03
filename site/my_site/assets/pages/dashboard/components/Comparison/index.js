/**
 * Comparison Dashboard Component
 * Tab 2: Topic list + donut charts with country breakdown drawer
 */

import React, { useState, useEffect, useCallback } from "react";
import { DonutChart } from "../DonutChart";
import { CountryBreakdownModal } from "../CountryBreakdownModal";
import { fetchSurveySections, fetchSurveyQuestions } from "../../api";

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
  const [topics, setTopics] = useState([]);
  const [topicsLoading, setTopicsLoading] = useState(true);
  const [topicsError, setTopicsError] = useState(null);

  const [allQuestions, setAllQuestions] = useState([]);
  const [questionsLoading, setQuestionsLoading] = useState(true);
  const [questionsError, setQuestionsError] = useState(null);

  const [selectedTopic, setSelectedTopic] = useState(null);
  const [showPerRegion, setShowPerRegion] = useState(false);
  const [activeBreakdown, setActiveBreakdown] = useState(null);

  // Closed questions whose section matches the selected topic's numeric ID
  const filteredQuestions = allQuestions.filter(
    (q) => q.type === "Closed" && q.section === selectedTopic
  );

  useEffect(() => {
    // Fetch sections and questions in parallel
    Promise.all([fetchSurveySections(), fetchSurveyQuestions()])
      .then(([sections, questions]) => {
        setTopics(sections);
        if (sections.length > 0) setSelectedTopic(sections[0].id);
        setAllQuestions(questions);
      })
      .catch((err) => {
        console.error("Failed to load comparison data:", err);
        setTopicsError(err.message);
        setQuestionsError(err.message);
      })
      .finally(() => {
        setTopicsLoading(false);
        setQuestionsLoading(false);
      });
  }, []);

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
          {topicsLoading && (
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="topic-card topic-card--skeleton">
                <span className="topic-icon skeleton-icon" />
                <span className="topic-label skeleton-text" />
                <span className="topic-radio" />
              </div>
            ))
          )}
          {topicsError && (
            <div className="topic-list-error">Failed to load topics: {topicsError}</div>
          )}
          {!topicsLoading && !topicsError && topics.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`topic-card ${selectedTopic === t.id ? "active" : ""}`}
              onClick={() => setSelectedTopic(t.id)}
            >
              <span className="topic-icon">
                <MedalIcon />
              </span>
              <span className="topic-label">{t.title}</span>
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
            {questionsLoading && (
              Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="donut-chart-skeleton" />
              ))
            )}
            {questionsError && (
              <div className="questions-error">Failed to load questions: {questionsError}</div>
            )}
            {!questionsLoading && !questionsError && filteredQuestions.map((q, i) => {
              const breakdownKey = `${selectedTopic}-${i}`;
              return (
                <DonutChart
                  key={`${selectedTopic}-${q.number}`}
                  chartData={{ label: `${q.number}. ${q.short_name ?? q.text}`, yes: 0, no: 0, total: 0 }}
                  showPerRegion={showPerRegion}                  description={q.long_description || q.description || undefined}                  onViewBreakdown={
                    !showPerRegion ? () => openBreakdown(breakdownKey, q.short_name) : null
                  }
                />
              );
            })}
            {!questionsLoading && !questionsError && filteredQuestions.length === 0 && (
              <p className="no-questions">No closed questions for this section.</p>
            )}
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
