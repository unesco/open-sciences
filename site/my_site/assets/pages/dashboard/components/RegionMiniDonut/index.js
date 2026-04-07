/**
 * RegionMiniDonut
 * A scaled-down doughnut chart with orbital floating callout labels,
 * used inside each region card in the RegionBreakdownModal drawer.
 */

import React, { useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { loadScript, getAnswerColor } from "../utils";
import { CHARTJS_CDN_URL, CHARTJS_CDN_ID } from "../../constants";

export function RegionMiniDonut({ regionName, answerEntries, total }) {
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

  // ── Floating label geometry (scaled down for drawer width) ──────────────
  const CX      = 130;
  const CY      = 120;
  const R       = 58;
  const LABEL_H = 46;
  const MIN_GAP = 6;

  let cumDeg = -90;
  const items = answerEntries.map(({ name, count, colorIdx }) => {
    const pct     = total ? Math.round((count / total) * 100) : 0;
    const frac    = total > 0 ? count / total : 0;
    const spanDeg = frac * 360;
    const midDeg  = cumDeg + spanDeg / 2;
    cumDeg       += spanDeg;
    const midRad  = (midDeg * Math.PI) / 180;
    return {
      name, pct,
      lx:      CX + R * Math.cos(midRad),
      ly:      CY + R * Math.sin(midRad),
      onRight: Math.cos(midRad) >= 0,
      colorIdx,
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

  return (
    <div className="rbd-mini-wrap">
      <div className="rbd-mini-float-wrap">
        <div className="donut-canvas-wrap">
          <canvas ref={canvasRef} />
          <div className="rbd-mini-center">
            <div className="rbd-mini-count">{total}</div>
            <div className="rbd-mini-region">{regionName}</div>
          </div>
        </div>
        {items.map(({ name, pct, lx, ly, onRight, colorIdx }) => (
          <div
            key={name}
            className="donut-float-label"
            style={{
              left:      lx,
              top:       ly,
              transform: `translate(${onRight ? "0%" : "-100%"}, -50%)`,
            }}
          >
            <span className="donut-float-dot" style={{ background: getAnswerColor(name, colorIdx) }} />
            <span className="donut-float-text">{name}, {pct}%</span>
          </div>
        ))}
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
