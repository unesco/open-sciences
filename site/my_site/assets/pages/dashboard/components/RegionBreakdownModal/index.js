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

function RegionCard({ regionName, data }) {
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

  // Build per-region data — all answers
  const regionData = {};
  if (countryToRegion && Object.keys(countryToRegion).length > 0) {
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
  }

  // Only show regions that have at least 1 response
  const regions       = Object.entries(regionData).filter(([, d]) => d.total > 0).sort((a, b) => b[1].total - a[1].total);
  const isLoading     = !countryToRegion || Object.keys(countryToRegion).length === 0;
  const displayRegions = regions;

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
          {!isLoading && displayRegions.length === 0 && <p className="breakdown-no-data">No region data available.</p>}
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

