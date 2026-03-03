/**
 * DonutChart Component
 * Renders a Chart.js doughnut chart for survey response data
 */

import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import PropTypes from "prop-types";
import { loadScript } from "../utils";

export const DonutChart = ({ chartData, showPerRegion, onViewBreakdown, description }) => {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);
  const [showInfo, setShowInfo] = useState(false);

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

      const factor = showPerRegion ? 0.65 : 1;
      const yes = Math.round(chartData.yes * factor);
      const no = chartData.total - yes;

      chartRef.current = new window.Chart(canvasRef.current.getContext("2d"), {
        type: "doughnut",
        data: {
          labels: [
            `No,${no} (${Math.round((no / chartData.total) * 100)}%)`,
            `Yes, ${yes} (${Math.round((yes / chartData.total) * 100)}%)`,
          ],
          datasets: [
            {
              data: [no, yes],
              backgroundColor: ["#555", "#0073b7"],
              borderWidth: 2,
              borderColor: "#fff",
            },
          ],
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

  const factor = showPerRegion ? 0.65 : 1;
  const yes = Math.round(chartData.yes * factor);
  const no = chartData.total - yes;

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
        <div className="donut-label donut-label-no">
          <span className="donut-label-dot donut-label-dot-grey" />
          No,{no} ({Math.round((no / chartData.total) * 100)}%)
        </div>

        <div className="donut-canvas-wrap">
          <canvas ref={canvasRef} />
          <div className="donut-center">
            <div className="donut-total">{chartData.total}</div>
            <div className="donut-label-text">Responses</div>
          </div>
        </div>

        <div className="donut-label donut-label-yes">
          <span className="donut-label-dot donut-label-dot-blue" />
          Yes, {yes} ({Math.round((yes / chartData.total) * 100)}%)
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
    yes: PropTypes.number.isRequired,
    no: PropTypes.number.isRequired,
    total: PropTypes.number.isRequired,
  }).isRequired,
  showPerRegion: PropTypes.bool,
  onViewBreakdown: PropTypes.func,
  description: PropTypes.string,
};
