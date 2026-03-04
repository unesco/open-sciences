/**
 * CountryBreakdownModal Component
 * Slide-in drawer showing per-country breakdown for a survey question.
 * Data is driven entirely from live survey responses - no hardcoded lookup needed.
 */

import React, { useEffect } from "react";
import PropTypes from "prop-types";

// ─── Blue-shade palette (mirrors DonutChart) ─────────────────────────────

const BLUE_PALETTE = [
  "#0d3b6e", // deep navy
  "#1a6fa8", // primary blue
  "#3a9bd5", // medium blue
  "#6db8e8", // light blue
  "#a3d4f5", // pale blue
  "#c8e6f9", // very pale blue
];

function getAnswerColor(index) {
  return BLUE_PALETTE[index % BLUE_PALETTE.length];
}

// ─── Component ─────────────────────────────────────────────────────────────

/**
 * @param {string}  chartLabel         Question label shown in the drawer header
 * @param {Object}  countriesByAnswer  Map: { [answerName]: [countryName, ...] }
 * @param {Function} onClose           Called when the drawer should close
 */
export const CountryBreakdownModal = ({ chartLabel, countriesByAnswer, onClose }) => {
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  // Build sections from live data
  const entries = Object.entries(countriesByAnswer || {});
  const total = entries.reduce((sum, [, countries]) => sum + countries.length, 0);

  const sections = entries
    .map(([answerName, countries], index) => ({
      key: answerName,
      label: answerName,
      dot: getAnswerColor(index),
      count: countries.length,
      pct: total > 0 ? Math.round((countries.length / total) * 100) : 0,
      countries: [...countries].sort(),
    }))
    .sort((a, b) => b.count - a.count); // dominant answer first

  const hasData = sections.length > 0 && total > 0;

  return (
    <>
      {/* Backdrop */}
      <div
        className="breakdown-backdrop"
        role="button"
        tabIndex={0}
        aria-label="Close breakdown"
        onClick={onClose}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onClose(); }}
      />

      {/* Drawer panel */}
      <div className="breakdown-drawer" role="dialog" aria-modal="true" aria-label="Country breakdown">
        <div className="breakdown-header">
          <h3 className="breakdown-title">
            {chartLabel}
            <span className="breakdown-info-icon" title="Survey question">ⓘ</span>
          </h3>
          <button type="button" className="breakdown-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="breakdown-body">
          {!hasData && (
            <p className="breakdown-no-data">No country data available for this question.</p>
          )}

          {hasData && sections.map((section) => (
            <div key={section.key} className="breakdown-section">
              <div className="breakdown-section-heading">
                <span className="breakdown-dot" style={{ background: section.dot }} />
                <span className="breakdown-section-label">
                  {section.label}, {section.pct}%
                  <span className="breakdown-section-count">
                    {" "}({section.count} {section.count === 1 ? "response" : "responses"})
                  </span>
                </span>
              </div>

              {section.countries.length > 0 && (
                <div className="breakdown-country-grid">
                  {section.countries.map((c) => (
                    <button key={c} type="button" className="breakdown-country-link">
                      {c}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}

          {hasData && (
            <p className="breakdown-total-note">
              Total responses: <strong>{total}</strong>
            </p>
          )}
        </div>
      </div>
    </>
  );
};

CountryBreakdownModal.propTypes = {
  chartLabel:        PropTypes.string.isRequired,
  countriesByAnswer: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.string)),
  onClose:           PropTypes.func.isRequired,
};

CountryBreakdownModal.defaultProps = {
  countriesByAnswer: {},
};
