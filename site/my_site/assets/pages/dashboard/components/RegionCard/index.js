/**
 * RegionCard
 * One card per UNESCO region: mini donut with orbital labels + answer legend
 * with country lists. Used inside RegionBreakdownModal.
 */

import React from "react";
import PropTypes from "prop-types";
import { getAnswerColor } from "../utils";
import { RegionMiniDonut } from "../RegionMiniDonut";

const ANSWER_PRIORITY = ["yes", "partial", "ongoing", "no answer", "no"];

function findIso3(countriesList, countryName) {
  if (!countriesList || !countryName) return null;
  const match = countriesList.find(
    (c) => c.name && c.name.toLowerCase() === countryName.toLowerCase()
  );
  return match ? match.iso_3 : null;
}

function sortAnswerEntries(entries) {
  return entries.slice().sort((a, b) => {
    const ai = ANSWER_PRIORITY.indexOf(a.name.toLowerCase().trim());
    const bi = ANSWER_PRIORITY.indexOf(b.name.toLowerCase().trim());
    const aRank = ai === -1 ? ANSWER_PRIORITY.length : ai;
    const bRank = bi === -1 ? ANSWER_PRIORITY.length : bi;
    return aRank - bRank;
  });
}

export function RegionCard({ regionName, data, countriesList, onCountryClick }) {
  const answerEntries = sortAnswerEntries(
    Object.entries(data.answers).map(([name, count], i) => ({ name, count, colorIdx: i }))
  );

  return (
    <div className="rbd-region-card">
      <RegionMiniDonut
        regionName={regionName}
        answerEntries={answerEntries}
        total={data.total}
      />
      <div className="rbd-region-legend">
        {answerEntries.map((entry) => {
          const pct       = data.total ? Math.round((entry.count / data.total) * 100) : 0;
          const countries = (data.countries[entry.name] || []).slice().sort();
          return (
            <div key={entry.name} className="rbd-legend-section">
              <div className="rbd-legend-heading">
                <span className="rbd-legend-dot" style={{ background: getAnswerColor(entry.name, entry.colorIdx) }} />
                <span className="rbd-legend-label">{entry.name}, {pct}%</span>
              </div>
              {countries.length > 0 && (
                <div className="rbd-legend-countries">
                  {countries.map((c, ci) => {
                    const iso3 = findIso3(countriesList, c);
                    const clickable = iso3 && onCountryClick;
                    return (
                      <span key={c}>
                        {clickable ? (
                          <button
                            type="button"
                            className="rbd-country-link"
                            onClick={() => onCountryClick(iso3, c)}
                          >
                            {c}
                          </button>
                        ) : (
                          <span className="rbd-country-name">{c}</span>
                        )}
                        {ci < countries.length - 1 ? ", " : ""}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

RegionCard.propTypes = {
  regionName: PropTypes.string.isRequired,
  data: PropTypes.shape({
    answers:   PropTypes.objectOf(PropTypes.number).isRequired,
    countries: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.string)).isRequired,
    total:     PropTypes.number.isRequired,
  }).isRequired,
  countriesList: PropTypes.arrayOf(PropTypes.shape({
    name:  PropTypes.string,
    iso_3: PropTypes.string,
  })),
  onCountryClick: PropTypes.func,
};

RegionCard.defaultProps = {
  countriesList:  [],
  onCountryClick: undefined,
};
