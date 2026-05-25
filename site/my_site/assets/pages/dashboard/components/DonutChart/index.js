/**
 * DonutChart Component
 * Renders a Chart.js doughnut chart for survey response data.
 * When showPerRegion is ON and countryToRegion is provided, shows the
 * regional distribution of the dominant answer (e.g. which regions said "Yes").
 */

import React, { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import { loadScript, getAnswerColor } from "../utils";
import { InfoIcon } from "../InfoIcon";
import { BLUE_PALETTE, CHARTJS_CDN_URL, CHARTJS_CDN_ID } from "../../constants";

/**
 * Compute what the chart should display.
 * In region mode: regional distribution of the Yes answer.
 * In normal mode: answer distribution.
 */
function computeDisplay(chartData, showPerRegion, countriesByAnswer, countryToRegion) {
  const answers = chartData.answers || {};
  const total   = chartData.total   || 0;

  if (showPerRegion && countryToRegion && Object.keys(countryToRegion).length > 0) {
    // Only use countries that answered "Yes"
    const yesCountries = (countriesByAnswer || {})["Yes"] || [];
    const allCountriesSet = new Set(yesCountries);

    // Count how many "Yes" countries per region (only regions with > 0 countries)
    const regionCounts = {};
    allCountriesSet.forEach((c) => {
      const r = countryToRegion[c];
      if (r) regionCounts[r] = (regionCounts[r] || 0) + 1;
    });

    const displayEntries = Object.entries(regionCounts).filter(([, n]) => n > 0).sort((a, b) => b[1] - a[1]);
    return {
      displayEntries,
      displayTotal:  allCountriesSet.size,
      centerLabel:   allCountriesSet.size > 0 ? "Yes" : null,
      isRegionMode:  true,
    };
  }

  return {
    displayEntries: Object.entries(answers),
    displayTotal:   total,
    centerLabel:    null,
    isRegionMode:   false,
  };
}

export const DonutChart = ({
  chartData,
  showPerRegion,
  onViewBreakdown,
  description,
  options,
  countriesByAnswer,
  countryToRegion,
}) => {
  const canvasRef      = useRef(null);
  const chartRef       = useRef(null);
  // Tracks current display state so the hover effect can use the right colors
  const displayStateRef = useRef({ entries: [], isRegionMode: false });

  const [hoveredIndex,  setHoveredIndex]  = useState(null);

  // ── Hover: dim non-hovered segments ─────────────────────────────────────
  useEffect(() => {
    if (!chartRef.current) return;
    const { entries, isRegionMode } = displayStateRef.current;
    const dataset = chartRef.current.data.datasets[0];
    const len     = dataset.data.length;

    dataset.backgroundColor = Array.from({ length: len }, (_, i) => {
      const [name] = entries[i] || [""];
      const color  = isRegionMode
        ? BLUE_PALETTE[i % BLUE_PALETTE.length]
        : getAnswerColor(name, i);
      if (hoveredIndex === null) return color;
      return i === hoveredIndex ? color : `${color}4d`;
    });
    dataset.hoverOffset = Array.from({ length: len }, (_, i) =>
      i === hoveredIndex ? 10 : 0
    );
    chartRef.current.update("none");
  }, [hoveredIndex]);

  // ── Build / rebuild Chart.js instance ──────────────────────────────────
  useEffect(() => {
    let mounted = true;
    (async () => {
      await loadScript(CHARTJS_CDN_URL, CHARTJS_CDN_ID);
      if (!mounted || !canvasRef.current || !window.Chart) return;
      if (chartRef.current) { chartRef.current.destroy(); }

      const { displayEntries, isRegionMode } = computeDisplay(
        chartData, showPerRegion, countriesByAnswer, countryToRegion
      );

      // Save to ref so hover effect can read it without closing over stale data
      displayStateRef.current = { entries: displayEntries, isRegionMode };

      chartRef.current = new window.Chart(canvasRef.current.getContext("2d"), {
        type: "doughnut",
        data: {
          labels: displayEntries.map(([name]) => name),
          datasets: [{
            data:            displayEntries.map(([, count]) => count),
            backgroundColor: displayEntries.map(([name], i) =>
              isRegionMode ? BLUE_PALETTE[i % BLUE_PALETTE.length] : getAnswerColor(name, i)
            ),
            borderWidth:  2,
            borderColor: "#fff",
          }],
        },
        options: {
          cutout:   "65%",
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend:  { display: false },
            tooltip: { enabled: false },
          },
          hover: { mode: null },
        },
      });
    })();
    return () => {
      mounted = false;
      if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; }
    };
  }, [chartData, showPerRegion, countriesByAnswer, countryToRegion]);

  // ── Render-phase display data ────────────────────────────────────────────
  const { displayEntries, displayTotal, centerLabel, isRegionMode } = computeDisplay(
    chartData, showPerRegion, countriesByAnswer, countryToRegion
  );

  return (
    <div className="donut-card">
      <div className="donut-card-title">
        {chartData.label}
        <InfoIcon
          description={description}
          options={options}
          modalTitle={chartData.label}
        />
      </div>

      <div className="donut-chart-area">
        <div className="donut-float-wrap">
          {/* Canvas */}
          <div className="donut-canvas-wrap">
            <canvas ref={canvasRef} />
            <div className="donut-center">
              {centerLabel
                ? <div className="donut-total" style={{ fontSize: "1.1rem" }}>{centerLabel}</div>
                : <div className="donut-total">{displayTotal}</div>
              }
              <div className="donut-label-text">Responses</div>
            </div>
          </div>

          {/* Floating callout labels orbiting the ring */}
          {(() => {
            const CX      = 190;
            const CY      = 150;
            const R       = 82;
            const LABEL_H = 46;
            const MIN_GAP = 6;

            let cumDeg = -90;
            const items = displayEntries.map(([name, count], i) => {
              const pct     = displayTotal ? Math.round((count / displayTotal) * 100) : 0;
              const frac    = displayTotal > 0 ? count / displayTotal : 0;
              const spanDeg = frac * 360;
              const midDeg  = cumDeg + spanDeg / 2;
              cumDeg       += spanDeg;
              const midRad  = (midDeg * Math.PI) / 180;
              return {
                name, count, pct, i,
                lx:      CX + R * Math.cos(midRad),
                ly:      CY + R * Math.sin(midRad),
                onRight: Math.cos(midRad) >= 0,
              };
            });

            const MIN_Y = 16;
            const MAX_Y = CY * 2 - 16;
            [true, false].forEach((side) => {
              const grp = items.filter((d) => d.onRight === side).sort((a, b) => a.ly - b.ly);
              for (let iter = 0; iter < 40; iter++) {
                for (let j = 1; j < grp.length; j++) {
                  const a = grp[j - 1];
                  const b = grp[j];
                  const overlap = (a.ly + LABEL_H + MIN_GAP) - b.ly;
                  if (overlap > 0) { a.ly -= overlap / 2; b.ly += overlap / 2; }
                }
                grp.forEach((d) => { d.ly = Math.max(MIN_Y, Math.min(MAX_Y, d.ly)); });
              }
            });

            return items.map(({ name, count, pct, i, lx, ly, onRight }) => {
              const color = isRegionMode
                ? BLUE_PALETTE[i % BLUE_PALETTE.length]
                : getAnswerColor(name, i);
              return (
                <div
                  key={name}
                  className={`donut-float-label${hoveredIndex === i ? " donut-float-label--active" : ""}`}
                  style={{
                    left:      lx,
                    top:       ly,
                    transform: `translate(${onRight ? "0%" : "-100%"}, -50%)`,
                  }}
                  onMouseEnter={() => setHoveredIndex(i)}
                  onMouseLeave={() => setHoveredIndex(null)}
                >
                  <span className="donut-float-dot" style={{ background: color }} />
                  <span className="donut-float-text">
                    {isRegionMode ? `${name} (${pct}%)` : `${name}, ${count} (${pct}%)`}
                  </span>
                </div>
              );
            });
          })()}
        </div>
      </div>

      {!showPerRegion && onViewBreakdown && (
        <button type="button" className="breakdown-btn" onClick={onViewBreakdown}>
          <img src="/static/images/menu_icon.png" alt="" aria-hidden="true" className="breakdown-btn-icon" />
          View country breakdown
        </button>
      )}
      {showPerRegion && onViewBreakdown && (
        <button type="button" className="breakdown-btn" onClick={onViewBreakdown}>
          <img src="/static/images/menu_icon.png" alt="" aria-hidden="true" className="breakdown-btn-icon" />
          View region breakdown
        </button>
      )}
    </div>
  );
};

DonutChart.propTypes = {
  chartData: PropTypes.shape({
    label:   PropTypes.string.isRequired,
    answers: PropTypes.objectOf(PropTypes.number),
    total:   PropTypes.number.isRequired,
  }).isRequired,
  showPerRegion:     PropTypes.bool,
  onViewBreakdown:   PropTypes.func,
  description:       PropTypes.string,
  options:           PropTypes.arrayOf(PropTypes.shape({ code: PropTypes.string, label: PropTypes.string })),
  countriesByAnswer: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.string)),
  countryToRegion:   PropTypes.objectOf(PropTypes.string),
};

DonutChart.defaultProps = {
  showPerRegion:     false,
  onViewBreakdown:   undefined,
  description:       undefined,
  countriesByAnswer: {},
  countryToRegion:   {},
};
