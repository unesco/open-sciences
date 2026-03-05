/**
 * RegionBreakdownModal
 * Side drawer (slide-in from right) showing per-region breakdown.
 * For each UNESCO region: mini donut + answer legend + country list.
 * countryToRegion is fetched by Comparison and passed as a prop.
 */

import React, { useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { loadScript, getAnswerColor } from "../utils";
import { CHARTJS_CDN_URL, CHARTJS_CDN_ID } from "../../constants";

// ─── Mini donut (no orbital labels) ─────────────────────────────────────────

function RegionMiniDonut({ regionName, answerEntries, total }) {
  const canvasRef = useRef(null);
  const chartRef  = useRef(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      await loadScript(CHARTJS_CDN_URL, CHARTJS_CDN_ID);
      if (!mounted || !canvasRef.current || !window.Chart) return;
      if (chartRef.current) { chartRef.current.destroy(); }
      chartRef.current = new window.Chart(canvasRef.current.getContext("2d"), {
        type: "doughnut",
        data: {
          labels: answerEntries.map((e) => e.name),
          datasets: [{
            data:            answerEntries.map((e) => e.count),
            backgroundColor: answerEntries.map((e) => getAnswerColor(e.name, e.colorIdx)),
            borderWidth: 2,
            borderColor: "#fff",
          }],
        },
        options: {
          cutout: "65%",
          responsive: false,
          maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          hover: { mode: null },
        },
      });
    })();
    return () => {
      mounted = false;
      if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="rbd-mini-wrap">
      <div className="rbd-mini-canvas-wrap">
        <canvas ref={canvasRef} width="110" height="110" />
        <div className="rbd-mini-center">
          <div className="rbd-mini-count">{total}</div>
          <div className="rbd-mini-region">{regionName}</div>
        </div>
      </div>
    </div>
  );
}

RegionMiniDonut.propTypes = {
  regionName:    PropTypes.string.isRequired,
  answerEntries: PropTypes.arrayOf(PropTypes.shape({
    name:     PropTypes.string,
    count:    PropTypes.number,
    colorIdx: PropTypes.number,
  })).isRequired,
  total: PropTypes.number.isRequired,
};

// ─── Region card: mini donut + legend ────────────────────────────────────────

function RegionCard({ regionName, data }) {
  const yesCount     = data.answers["Yes"] || 0;
  const yesCountries = (data.countries["Yes"] || []).slice().sort();
  const answerEntries = [{ name: "Yes", count: yesCount, colorIdx: 0 }];

  return (
    <div className="rbd-region-card">
      <RegionMiniDonut
        regionName={regionName}
        answerEntries={answerEntries}
        total={data.total}
      />
      <div className="rbd-region-legend">
        <div className="rbd-legend-section">
          <div className="rbd-legend-heading">
            <span className="rbd-legend-dot" style={{ background: getAnswerColor("Yes", 0) }} />
            <span className="rbd-legend-label">Yes — {yesCount} countr{yesCount === 1 ? "y" : "ies"}</span>
          </div>
          {yesCountries.length > 0 && (
            <div className="rbd-legend-countries">
              {yesCountries.map((c, ci) => (
                <span key={c} className="rbd-country-name">
                  {c}{ci < yesCountries.length - 1 ? ", " : ""}
                </span>
              ))}
            </div>
          )}
        </div>
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

// ─── Main drawer ─────────────────────────────────────────────────────────────

export const RegionBreakdownModal = ({
  chartLabel,
  description,
  countriesByAnswer,
  countryToRegion,
  onClose,
}) => {
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  // Build per-region data — only "Yes" answers (case-insensitive key lookup)
  const yesKey = Object.keys(countriesByAnswer || {}).find(
    (k) => k.toLowerCase().trim() === "yes"
  );
  const yesCountries = yesKey ? (countriesByAnswer[yesKey] || []) : [];
  const regionData = {};
  if (countryToRegion && Object.keys(countryToRegion).length > 0) {
    yesCountries.forEach((country) => {
      const region = countryToRegion[country] || "Other";
      if (!regionData[region]) regionData[region] = { answers: {}, countries: {}, total: 0 };
      regionData[region].answers["Yes"]  = (regionData[region].answers["Yes"] || 0) + 1;
      if (!regionData[region].countries["Yes"]) regionData[region].countries["Yes"] = [];
      regionData[region].countries["Yes"].push(country);
      regionData[region].total += 1;
    });
  }

  const regions   = Object.entries(regionData).sort((a, b) => b[1].total - a[1].total);
  const isLoading = !countryToRegion || Object.keys(countryToRegion).length === 0;

  // When no Yes answers exist, still show all known regions with 0 count
  const displayRegions = regions.length > 0
    ? regions
    : Object.keys(
        Object.values(countryToRegion || {}).reduce((acc, region) => { acc[region] = true; return acc; }, {})
      )
        .sort()
        .map((region) => [region, { answers: { Yes: 0 }, countries: { Yes: [] }, total: 0 }]);

  return (
    <>
      {/* Same backdrop + drawer classes as CountryBreakdownModal */}
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
            {description && (
              <span className="breakdown-info-icon" title={description}>ⓘ</span>
            )}
          </h3>
          <button type="button" className="breakdown-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="rbd-subheader">View per region</div>

        <div className="breakdown-body rbd-body">
          {isLoading && <p className="breakdown-no-data">Loading region data…</p>}
          {!isLoading && displayRegions.map(([regionName, data]) => (
            <RegionCard
              key={regionName}
              regionName={regionName}
              data={data}
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
  onClose:           PropTypes.func.isRequired,
};

RegionBreakdownModal.defaultProps = {
  description:       undefined,
  countriesByAnswer: {},
  countryToRegion:   {},
};

