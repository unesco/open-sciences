/**
 * Comparison Dashboard Component
 * Tab 2: Topic list + donut charts with country breakdown drawer
 */

import React, { useState, useEffect, useCallback } from "react";
import PropTypes from "prop-types";
import { DonutChart } from "../DonutChart";
import { CountryBreakdownModal } from "../CountryBreakdownModal";
import { RegionBreakdownModal } from "../RegionBreakdownModal";
import { fetchSurveySections, fetchSurveyQuestions, fetchSurveyResponsesByQuestion, fetchCountries, surveyResponsesDownloadUrl } from "../../api";
import { decodeHtmlEntities, parseClosedAnswerOptions, normaliseAnswerName } from "../utils";
import { DownloadMenu } from "../DownloadMenu";

/**
 * Build a lookup map: question_number → { answers: { [answerName]: count }, total }
 * Only counts rows with question_type === "Closed".
 * All distinct answer_closed_name values are tallied dynamically.
 */
function buildResponsesMap(responses) {
  const map = {};
  responses.forEach((r) => {
    // Only closed questions are fetched, but guard defensively
    if (r.question_type && r.question_type !== "Closed") return;
    const num = r.question_number;
    if (!map[num]) map[num] = { answers: {}, countries: {}, total: 0 };
    const answer = normaliseAnswerName(r.answer_closed_name);
    map[num].answers[answer] = (map[num].answers[answer] || 0) + 1;
    if (r.country_name) {
      if (!map[num].countries[answer]) map[num].countries[answer] = [];
      // avoid duplicates if a country submitted multiple times
      if (!map[num].countries[answer].includes(r.country_name)) {
        map[num].countries[answer].push(r.country_name);
      }
    }
    map[num].total += 1;
  });
  return map;
}

// ─── Comparison component ──────────────────────────────────────────────────

export const Comparison = ({ onCountryClick }) => {
  const [topics, setTopics] = useState([]);
  const [topicsLoading, setTopicsLoading] = useState(true);
  const [topicsError, setTopicsError] = useState(null);

  const [allQuestions, setAllQuestions] = useState([]);
  const [questionsLoading, setQuestionsLoading] = useState(true);
  const [questionsError, setQuestionsError] = useState(null);

  const [responsesMap, setResponsesMap] = useState({});
  const [responsesLoading, setResponsesLoading] = useState(false);

  const [selectedTopic, setSelectedTopic] = useState(null);
  const [showPerRegion, setShowPerRegion] = useState(false);
  const [activeBreakdown, setActiveBreakdown] = useState(null);
  const [countryToRegion, setCountryToRegion] = useState({});
  const [countriesList, setCountriesList] = useState([]);

  // Closed questions whose section matches the selected topic.
  // Stringify both sides so numeric IDs from one API and string IDs from
  // another still match (e.g. section.id === 1 vs question.section === "1").
  const filteredQuestions = allQuestions.filter(
    (q) => q.type === "Closed" && String(q.section) === String(selectedTopic)
  );

  // On mount: load country→region map, sections, and questions in parallel
  useEffect(() => {
    fetchCountries()
      .then((countries) => {
        const map = {};
        countries.forEach(({ name, region }) => {
          if (name && region) map[name] = decodeHtmlEntities(region);
        });
        setCountryToRegion(map);
        setCountriesList(countries);
      })
      .catch((err) => console.error("Failed to load countries:", err));
  }, []);

  useEffect(() => {
    Promise.all([fetchSurveySections(), fetchSurveyQuestions()])
      .then(([sections, questions]) => {
        setTopics(sections);
        setAllQuestions(questions);
        if (sections.length > 0) setSelectedTopic(sections[0].id);
      })
      .catch((err) => {
        console.error("Failed to load sections/questions:", err);
        setTopicsError(err.message);
        setQuestionsError(err.message);
      })
      .finally(() => {
        setTopicsLoading(false);
        setQuestionsLoading(false);
      });
  }, []);

  // When selected section changes: fire one API call per question number in
  // parallel, then merge all results into a single responses map.
  useEffect(() => {
    if (!selectedTopic || allQuestions.length === 0) return;

    const questionNumbers = allQuestions
      .filter((q) => q.type === "Closed" && String(q.section) === String(selectedTopic))
      .map((q) => q.number)
      .filter(Boolean);

    if (questionNumbers.length === 0) return;

    setResponsesLoading(true);
    setResponsesMap({});

    // One request per question number, all in parallel
    Promise.all(questionNumbers.map((num) => fetchSurveyResponsesByQuestion(num)))
      .then((results) => {
        // Flatten all per-question arrays into one and build the map
        const allResponses = results.flat();
        setResponsesMap(buildResponsesMap(allResponses));
      })
      .catch((err) => console.error("Failed to load responses:", err))
      .finally(() => setResponsesLoading(false));
  }, [selectedTopic, allQuestions]);

  const openBreakdown = useCallback((key, label, countries, description, mode) => {
    setActiveBreakdown({ key, label, countries, description, mode: mode || "country" });
  }, []);

  const closeBreakdown = useCallback(() => setActiveBreakdown(null), []);

  return (
    <div className="dash-comparison">
      <div className="dashboard-subheader">
        <strong>Select the topic to filter</strong>
        <DownloadMenu
          filteredHref={
            selectedTopic
              ? surveyResponsesDownloadUrl({ section_id: selectedTopic })
              : ""
          }
          allHref={surveyResponsesDownloadUrl()}
        />
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
                <img src="/static/images/menu_icon.png" alt="Section icon" className="topic-medal-icon" />
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
            {(questionsLoading || responsesLoading) && (
              Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="donut-chart-skeleton" />
              ))
            )}
            {questionsError && (
              <div className="questions-error">Failed to load questions: {questionsError}</div>
            )}
            {!questionsLoading && !responsesLoading && !questionsError && filteredQuestions.map((q, i) => {
              const stats       = responsesMap[q.number] || { answers: {}, countries: {}, total: 0 };
              const breakdownKey = `${selectedTopic}-${i}`;
              const desc         = q.long_description || q.description || undefined;
              const qOptions     = parseClosedAnswerOptions(q.closed_answer_options);
              return (
                <DonutChart
                  key={`${selectedTopic}-${q.number}`}
                  chartData={{
                    label: `${q.short_name || q.text}`,
                    answers: stats.answers,
                    total: stats.total,
                  }}
                  showPerRegion={showPerRegion}
                  description={desc}
                  options={qOptions}
                  countriesByAnswer={stats.countries}
                  countryToRegion={countryToRegion}
                  onViewBreakdown={
                    showPerRegion
                      ? () => openBreakdown(breakdownKey, q.short_name || q.text, stats.countries, desc, "region")
                      : () => openBreakdown(breakdownKey, q.short_name || q.text, stats.countries, desc, "country")
                  }
                />
              );
            })}
            {!questionsLoading && !responsesLoading && !questionsError && filteredQuestions.length === 0 && (
              <p className="no-questions">No closed questions for this section.</p>
            )}
            <p className="donut-footnote">*One response = one Member State</p>
          </div>
        </div>
      </div>

      {/* Country breakdown drawer (slide-in) */}
      {activeBreakdown && activeBreakdown.mode !== "region" && (
        <CountryBreakdownModal
          chartLabel={activeBreakdown.label}
          description={activeBreakdown.description}
          countriesByAnswer={activeBreakdown.countries || {}}
          countriesList={countriesList}
          onCountryClick={onCountryClick}
          onClose={closeBreakdown}
        />
      )}

      {/* Region breakdown drawer */}
      {activeBreakdown && activeBreakdown.mode === "region" && (
        <RegionBreakdownModal
          chartLabel={activeBreakdown.label}
          description={activeBreakdown.description}
          countriesByAnswer={activeBreakdown.countries || {}}
          countryToRegion={countryToRegion}
          countriesList={countriesList}
          onCountryClick={onCountryClick}
          onClose={closeBreakdown}
        />
      )}
    </div>
  );
};

Comparison.propTypes = {
  onCountryClick: PropTypes.func,
};

Comparison.defaultProps = {
  onCountryClick: undefined,
};
