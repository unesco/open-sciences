/**
 * CountryBreakdownModal Component
 * Slide-in drawer showing per-country breakdown for a survey question.
 * Data is driven entirely from live survey responses - no hardcoded lookup needed.
 */

import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { getAnswerColor, buildInfoDescription } from "../utils";

// ─── Helper: find ISO-3 code for a country name ─────────────────────────────

function findIso3(countriesList, countryName) {
  if (!countriesList || !countryName) return null;
  const match = countriesList.find(
    (c) => c.name && c.name.toLowerCase() === countryName.toLowerCase()
  );
  return match ? match.iso_3 : null;
}

// ─── Component ─────────────────────────────────────────────────────────────

/**
 * @param {string}  chartLabel         Question label shown in the drawer header
 * @param {Object}  countriesByAnswer  Map: { [answerName]: [countryName, ...] }
 * @param {Array}   countriesList      Full countries array with iso_3 codes
 * @param {Function} onCountryClick    Called with (iso3, name) when a country is clicked
 * @param {Function} onClose           Called when the drawer should close
 */
export const CountryBreakdownModal = ({ chartLabel, description, countriesByAnswer, countriesList, onCountryClick, onClose }) => {
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
      dot: getAnswerColor(answerName, index),
      count: countries.length,
      pct: total > 0 ? Math.round((countries.length / total) * 100) : 0,
      countries: [...countries].sort(),
    }))
    .sort((a, b) => b.count - a.count); // dominant answer first

  const hasData = sections.length > 0 && total > 0;
  const infoDescription = buildInfoDescription(description);

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
            {infoDescription && (
              <span className="breakdown-info-icon" title={infoDescription}>ⓘ</span>
            )}
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
                  {section.countries.map((c) => {
                    const iso3 = findIso3(countriesList, c);
                    return (
                      <button
                        key={c}
                        type="button"
                        className={`breakdown-country-link${iso3 && onCountryClick ? " breakdown-country-link--clickable" : ""}`}
                        onClick={() => {
                          if (iso3 && onCountryClick) {
                            onClose();
                            onCountryClick(iso3, c);
                          }
                        }}
                      >
                        {c}
                      </button>
                    );
                  })}
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
  description:       PropTypes.string,
  countriesByAnswer: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.string)),
  countriesList:     PropTypes.arrayOf(PropTypes.shape({
    name:  PropTypes.string,
    iso_3: PropTypes.string,
  })),
  onCountryClick:    PropTypes.func,
  onClose:           PropTypes.func.isRequired,
};

CountryBreakdownModal.defaultProps = {
  description:       undefined,
  countriesByAnswer: {},
  countriesList:     [],
  onCountryClick:    undefined,
};
