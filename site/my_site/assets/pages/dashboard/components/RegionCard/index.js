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

function sortAnswerEntries(entries) {
  return entries.slice().sort((a, b) => {
    const ai = ANSWER_PRIORITY.indexOf(a.name.toLowerCase().trim());
    const bi = ANSWER_PRIORITY.indexOf(b.name.toLowerCase().trim());
    const aRank = ai === -1 ? ANSWER_PRIORITY.length : ai;
    const bRank = bi === -1 ? ANSWER_PRIORITY.length : bi;
    return aRank - bRank;
  });
}

export function RegionCard({ regionName, data }) {
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
                  {countries.map((c, ci) => (
                    <span key={c} className="rbd-country-name">
                      {c}{ci < countries.length - 1 ? ", " : ""}
                    </span>
                  ))}
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
};
