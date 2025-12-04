/**
 * Activity Chart Component
 * Displays daily activity chart using Chart.js
 */

import React, { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";

export const ActivityChart = ({ data }) => {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);
  const [chartLoaded, setChartLoaded] = useState(false);

  // Load Chart.js dynamically
  useEffect(() => {
    if (window.Chart) {
      setChartLoaded(true);
      return;
    }

    const script = document.createElement("script");
    script.src =
      "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js";
    script.async = true;
    script.onload = () => setChartLoaded(true);
    document.head.appendChild(script);

    return () => {
      // Cleanup script if component unmounts before loading
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
  }, []);

  useEffect(() => {
    if (!canvasRef.current || !data || !chartLoaded || !window.Chart) {
      return;
    }

    // Destroy previous chart if exists
    if (chartRef.current) {
      chartRef.current.destroy();
    }

    const ctx = canvasRef.current.getContext("2d");

    // Extract data
    const labels = data.map((d) => {
      const date = new Date(d.date);
      return date.toLocaleDateString("it-IT", {
        month: "short",
        day: "numeric",
      });
    });
    const uploads = data.map((d) => d.uploads);
    const downloads = data.map((d) => d.downloads);

    // Create Chart.js chart with UNESCO colors
    chartRef.current = new window.Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Uploads",
            data: uploads,
            borderColor: "#0077C8",
            backgroundColor: "rgba(0, 119, 200, 0.1)",
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: "#0077C8",
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
          },
          {
            label: "Downloads",
            data: downloads,
            borderColor: "#00B398",
            backgroundColor: "rgba(0, 179, 152, 0.1)",
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: "#00B398",
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            position: "top",
            labels: {
              usePointStyle: true,
              padding: 15,
              font: {
                size: 13,
                weight: "500",
              },
            },
          },
          tooltip: {
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            padding: 12,
            titleFont: {
              size: 14,
              weight: "600",
            },
            bodyFont: {
              size: 13,
            },
            borderColor: "rgba(255, 255, 255, 0.1)",
            borderWidth: 1,
            displayColors: true,
            callbacks: {
              label: function (context) {
                return (
                  context.dataset.label +
                  ": " +
                  context.parsed.y.toLocaleString()
                );
              },
            },
          },
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
            ticks: {
              maxRotation: 45,
              minRotation: 0,
              font: {
                size: 11,
              },
            },
          },
          y: {
            beginAtZero: true,
            grid: {
              color: "rgba(0, 0, 0, 0.05)",
            },
            ticks: {
              font: {
                size: 11,
              },
              callback: function (value) {
                return value.toLocaleString();
              },
            },
          },
        },
      },
    });

    // Cleanup on unmount
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, [data, chartLoaded]);

  return (
    <div className="chart-card">
      <div className="chart-title">📊 Daily Activity (Last 30 Days)</div>
      <div className="chart-container">
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
};

ActivityChart.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      date: PropTypes.string.isRequired,
      uploads: PropTypes.number.isRequired,
      downloads: PropTypes.number.isRequired,
    })
  ).isRequired,
};
