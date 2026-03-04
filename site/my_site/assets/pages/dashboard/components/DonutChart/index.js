/**
 * DonutChart Component
 * Renders a Chart.js doughnut chart for survey response data
 */

import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import PropTypes from "prop-types";
import { loadScript } from "../utils";

// Blue-shade palette — darkest to lightest
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

export const DonutChart = ({ chartData, showPerRegion, onViewBreakdown, description }) => {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);
  const [showInfo, setShowInfo] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState(null);

  // Dim non-hovered segments, pop the hovered one
  useEffect(() => {
    if (!chartRef.current) return;
    const dataset = chartRef.current.data.datasets[0];
    const len = dataset.data.length;
    dataset.backgroundColor = Array.from({ length: len }, (_, i) => {
      if (hoveredIndex === null) return getAnswerColor(i);
      return i === hoveredIndex ? getAnswerColor(i) : `${getAnswerColor(i)}4d`;
    });
    dataset.hoverOffset = Array.from({ length: len }, (_, i) =>
      i === hoveredIndex ? 10 : 0
    );
    chartRef.current.update("none");
  }, [hoveredIndex]);

  // Mobile modal: close on Escape
  useEffect(() => {
    if (!showInfo) return;
    const onKey = (e) => e.key === "Escape" && setShowInfo(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [showInfo]);

  // Only open the portal modal on touch/no-hover devices (mobile)
  const handleIconClick = () => {
    if (window.matchMedia("(hover: none)").matches) {
      setShowInfo((v) => !v);
    }
  };

  useEffect(() => {
    let mounted = true;
    (async () => {
      await loadScript(
        "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js",
        "chartjs-cdn"
      );
      if (!mounted || !canvasRef.current || !window.Chart) return;
      if (chartRef.current) { chartRef.current.destroy(); }

      const answers = chartData.answers || {};
      const total   = chartData.total || 0;
      const factor  = showPerRegion ? 0.65 : 1;
      const entries = Object.entries(answers);
      const scaled  = entries.map(([name, count]) => Math.round(count * factor));

      chartRef.current = new window.Chart(canvasRef.current.getContext("2d"), {
        type: "doughnut",
        data: {
          labels: entries.map(([name]) => name),
          datasets: [{
            data: scaled,
            backgroundColor: entries.map((_, i) => getAnswerColor(i)),
            borderWidth: 2,
            borderColor: "#fff",
          }],
        },
        options: {
          cutout: "65%",
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
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
  }, [chartData, showPerRegion]);

  const answers = chartData.answers || {};
  const total   = chartData.total   || 0;
  const factor  = showPerRegion ? 0.65 : 1;
  const entries = Object.entries(answers);

  return (
    <div className="donut-card">
      <div className="donut-card-title">
        {chartData.label}
        {description && (
          <span className="info-icon-wrap">
            <span
              className="donut-info-icon"
              role="button"
              tabIndex={0}
              aria-label="Show question description"
              onClick={handleIconClick}
              onKeyDown={(e) => e.key === "Enter" && setShowInfo((v) => !v)}
            >
              ⓘ
            </span>
            {/* Desktop: pure-CSS hover tooltip, hidden on mobile via media query */}
            <span className="info-hover-tooltip" role="tooltip">
              {description}
            </span>
          </span>
        )}
      </div>
      {/* Mobile: portal modal (only rendered when showInfo is true on touch devices) */}
      {showInfo && description && createPortal(
        <div
          className="donut-info-modal-backdrop"
          role="presentation"
          onClick={(e) => e.target === e.currentTarget && setShowInfo(false)}
          onKeyDown={(e) => e.key === "Escape" && setShowInfo(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label={chartData.label}
            className="donut-info-modal"
          >
            <div className="donut-info-modal-header">
              <span className="donut-info-modal-title">{chartData.label}</span>
              <button
                type="button"
                className="donut-info-modal-close"
                aria-label="Close"
                onClick={() => setShowInfo(false)}
              >
                ✕
              </button>
            </div>
            <div className="donut-info-modal-body">
              <p>{description}</p>
            </div>
          </div>
        </div>,
        document.body
      )}
      <div className="donut-chart-area">
        {/* Floating-label donut — labels orbit the chart at each segment's midpoint */}
        <div className="donut-float-wrap">
          {/* Canvas centred inside the wrap */}
          <div className="donut-canvas-wrap">
            <canvas ref={canvasRef} />
            <div className="donut-center">
              <div className="donut-total">{total}</div>
              <div className="donut-label-text">Responses</div>
            </div>
          </div>

          {/* Floating callout labels — one per answer, orbiting the ring */}
          {(() => {
            // Container 380×300; canvas 160×160 centred at (190, 150)
            const CX = 190;
            const CY = 150;
            const R  = 82; // ring outer radius — labels anchor right at the ring edge
            const LABEL_H = 46;  // approximate pill height when text wraps to 2 lines
            const MIN_GAP = 6;   // minimum vertical gap between pills

            // ── Step 1: compute ideal mid-angle position for each entry ──
            let cumDeg = -90; // Chart.js starts at the top
            const items = entries.map(([name, count], i) => {
              const scaled   = Math.round(count * factor);
              const pct      = total ? Math.round((count / total) * 100) : 0;
              const frac     = total > 0 ? count / total : 0;
              const spanDeg  = frac * 360;
              const midDeg   = cumDeg + spanDeg / 2;
              cumDeg        += spanDeg;
              const midRad   = (midDeg * Math.PI) / 180;
              return {
                name, scaled, pct, i,
                lx:      CX + R * Math.cos(midRad),
                ly:      CY + R * Math.sin(midRad),
                onRight: Math.cos(midRad) >= 0,
              };
            });

            // ── Step 2: resolve vertical overlaps per side ──
            [true, false].forEach((side) => {
              const grp = items
                .filter((d) => d.onRight === side)
                .sort((a, b) => a.ly - b.ly);
              for (let iter = 0; iter < 30; iter++) {
                for (let j = 1; j < grp.length; j++) {
                  const a = grp[j - 1];
                  const b = grp[j];
                  const overlap = (a.ly + LABEL_H + MIN_GAP) - b.ly;
                  if (overlap > 0) {
                    a.ly -= overlap / 2;
                    b.ly += overlap / 2;
                  }
                }
              }
            });

            // ── Step 3: render ──
            return items.map(({ name, scaled, pct, i, lx, ly, onRight }) => (
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
                <span
                  className="donut-float-dot"
                  style={{ background: getAnswerColor(i) }}
                />
                <span className="donut-float-text">
                  {name}, {scaled} ({pct}%)
                </span>
              </div>
            ));
          })()}
        </div>
      </div>
      {!showPerRegion && onViewBreakdown && (
        <button type="button" className="breakdown-btn" onClick={onViewBreakdown}>
          View country breakdown
        </button>
      )}
    </div>
  );
};

DonutChart.propTypes = {
  chartData: PropTypes.shape({
    label: PropTypes.string.isRequired,
    answers: PropTypes.objectOf(PropTypes.number),
    total: PropTypes.number.isRequired,
  }).isRequired,
  showPerRegion: PropTypes.bool,
  onViewBreakdown: PropTypes.func,
  description: PropTypes.string,
};
