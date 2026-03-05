/**
 * RegionBreakdownModal
 * Side drawer (slide-in from right) showing per-region breakdown.
 * For each UNESCO region: mini donut + answer legend + country list.
 * countryToRegion is fetched by Comparison and passed as a prop.
 */

import React, { useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { loadScript } from "../utils";

// ─── Color helpers (must match DonutChart) ───────────────────────────────────

const BLUE_PALETTE = [
  "#0d3b6e",
  "#1a5c9e",
  "#3a9bd5",
  "#6db8e8",
  "#a3d4f5",
  "#c8e6f9",
];

function getAnswerColor(name, index) {
  const lower = (name || "").toLowerCase().trim();
  if (lower === "yes") return "#0077D4";
  if (lower === "no")  return "#E7E6E6";
  return BLUE_PALETTE[index % BLUE_PALETTE.length];
}

// ─── Mini donut (no orbital labels) ─────────────────────────────────────────

function RegionMiniDonut({ regionName, answerEntries, total }) {
  const canvasRef = useRef(null);
  const chartRef  = useRef(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      await loadScript(
        "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js",
        "chartjs-cdn"
      );
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

function RegionCard({ regionName, data, allAnswerNames }) {
  const answerEntries = [
    ...allAnswerNames
      .filter((n) => data.answers[n])
      .map((n) => ({ name: n, count: data.answers[n], colorIdx: allAnswerNames.indexOf(n) })),
    ...Object.keys(data.answers)
      .filter((n) => !allAnswerNames.includes(n))
      .map((n, j) => ({ name: n, count: data.answers[n], colorIdx: allAnswerNames.length + j })),
  ];

  return (
    <div className="rbd-region-card">
      <RegionMiniDonut
        regionName={regionName}
        answerEntries={answerEntries}
        total={data.total}
      />
      <div className="rbd-region-legend">
        {answerEntries
          .slice()
          .sort((a, b) => b.count - a.count)
          .map(({ name, count, colorIdx }) => {
            const pct       = data.total ? Math.round((count / data.total) * 100) : 0;
            const countries = (data.countries[name] || []).slice().sort();
            return (
              <div key={name} className="rbd-legend-section">
                <div className="rbd-legend-heading">
                  <span
                    className="rbd-legend-dot"
                    style={{ background: getAnswerColor(name, colorIdx) }}
                  />
                  <span className="rbd-legend-label">{name}, {pct}%</span>
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
  allAnswerNames: PropTypes.arrayOf(PropTypes.string).isRequired,
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

  const allAnswerNames = Object.keys(countriesByAnswer || {});

  // Build per-region data
  const regionData = {};
  if (countryToRegion && Object.keys(countryToRegion).length > 0) {
    Object.entries(countriesByAnswer || {}).forEach(([answerName, countryList]) => {
      countryList.forEach((country) => {
        const region = countryToRegion[country] || "Other";
        if (!regionData[region]) regionData[region] = { answers: {}, countries: {}, total: 0 };
        regionData[region].answers[answerName]  = (regionData[region].answers[answerName] || 0) + 1;
        if (!regionData[region].countries[answerName]) regionData[region].countries[answerName] = [];
        regionData[region].countries[answerName].push(country);
        regionData[region].total += 1;
      });
    });
  }

  const regions   = Object.entries(regionData).sort((a, b) => b[1].total - a[1].total);
  const isLoading = !countryToRegion || Object.keys(countryToRegion).length === 0;

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
          {!isLoading && regions.length === 0 && (
            <p className="breakdown-no-data">No regional data available for this question.</p>
          )}
          {!isLoading && regions.length > 0 && regions.map(([regionName, data]) => (
            <RegionCard
              key={regionName}
              regionName={regionName}
              data={data}
              allAnswerNames={allAnswerNames}
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

