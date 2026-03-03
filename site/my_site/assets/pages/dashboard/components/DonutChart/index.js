/**
 * DonutChart Component
 * Renders a Chart.js doughnut chart for survey response data
 */

import React, { useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { loadScript } from "../utils";

export const DonutChart = ({ chartData, showPerRegion, onViewBreakdown }) => {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

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
        <span className="donut-info-icon" title="Survey question">ⓘ</span>
      </div>
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
};
