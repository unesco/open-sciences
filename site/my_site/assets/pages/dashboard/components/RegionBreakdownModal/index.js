/**
 * RegionBreakdownModal
 * Side drawer (slide-in from right) showing per-region breakdown.
 * For each UNESCO region renders a RegionCard (mini donut + legend).
 * countryToRegion is fetched by Comparison and passed as a prop.
 */

import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { RegionCard } from "../RegionCard";
import { buildInfoDescription } from "../utils";

// ─── Pure helper: aggregate countriesByAnswer → per-region data ───────────────

function buildRegionData(countriesByAnswer, countryToRegion) {
  const regionData = {};
  Object.entries(countriesByAnswer || {}).forEach(([answer, countries]) => {
    countries.forEach((country) => {
      const region = countryToRegion[country] || "Other";
      if (!regionData[region]) regionData[region] = { answers: {}, countries: {}, total: 0 };
      regionData[region].answers[answer] = (regionData[region].answers[answer] || 0) + 1;
      if (!regionData[region].countries[answer]) regionData[region].countries[answer] = [];
      regionData[region].countries[answer].push(country);
      regionData[region].total += 1;
    });
  });
  return regionData;
}

// ─── Main drawer ──────────────────────────────────────────────────────────────

export const RegionBreakdownModal = ({
  chartLabel,
  description,
  countriesByAnswer,
  countryToRegion,
  countriesList,
  onCountryClick,
  onClose,
}) => {
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const isLoading = !countryToRegion || Object.keys(countryToRegion).length === 0;
  const infoDescription = buildInfoDescription(description);

  const regions = isLoading
    ? []
    : Object.entries(buildRegionData(countriesByAnswer, countryToRegion))
        .filter(([, d]) => d.total > 0)
        .sort((a, b) => b[1].total - a[1].total);

  return (
    <>
      <div
        className="breakdown-backdrop"
        role="button"
        tabIndex={0}
        aria-label="Close region breakdown"
        onClick={onClose}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onClose(); }}
      />

      <div className="breakdown-drawer" role="dialog" aria-modal="true" aria-label="Region breakdown">
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

        <div className="rbd-subheader">View per region</div>

        <div className="breakdown-body rbd-body">
          {isLoading && <p className="breakdown-no-data">Loading region data…</p>}
          {!isLoading && regions.length === 0 && (
            <p className="breakdown-no-data">No region data available.</p>
          )}
          {!isLoading && regions.map(([regionName, data]) => (
            <RegionCard
              key={regionName}
              regionName={regionName}
              data={data}
              countriesList={countriesList}
              onCountryClick={(iso3, name) => {
                onClose();
                if (onCountryClick) onCountryClick(iso3, name);
              }}
            />
          ))}
        </div>
      </div>
    </>
  );
};

RegionBreakdownModal.propTypes = {
  chartLabel:        PropTypes.string.isRequired,
  description:       PropTypes.string,
  countriesByAnswer: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.string)),
  countryToRegion:   PropTypes.objectOf(PropTypes.string),
  countriesList:     PropTypes.arrayOf(PropTypes.shape({
    name:  PropTypes.string,
    iso_3: PropTypes.string,
  })),
  onCountryClick:    PropTypes.func,
  onClose:           PropTypes.func.isRequired,
};

RegionBreakdownModal.defaultProps = {
  description:       undefined,
  countriesByAnswer: {},
  countryToRegion:   {},
  countriesList:     [],
  onCountryClick:    undefined,
};
