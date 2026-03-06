import { useEffect, useRef } from "react";
import { loadScript, getAnswerColor } from "../utils";
import { CHARTJS_CDN_URL, CHARTJS_CDN_ID } from "../../constants";

/**
 * Loads Chart.js via CDN and manages the full lifecycle of a doughnut
 * chart instance on the given canvas ref.
 * answerEntries: [{ name, count, colorIdx }]
 */
export function useChartInstance(canvasRef, answerEntries) {
  const chartRef = useRef(null);

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
}
