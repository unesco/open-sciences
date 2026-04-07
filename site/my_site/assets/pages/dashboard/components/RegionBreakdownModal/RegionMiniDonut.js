import React, { useRef } from "react";
import PropTypes from "prop-types";
import { getAnswerColor } from "../utils";
import { useChartInstance } from "./useChartInstance";
import { computeOrbitalLabels } from "./computeOrbitalLabels";

export function RegionMiniDonut({ regionName, answerEntries, total }) {
  const canvasRef = useRef(null);
  useChartInstance(canvasRef, answerEntries);

  const items = computeOrbitalLabels(answerEntries, total);

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
  regionName: PropTypes.string.isRequired,
  answerEntries: PropTypes.arrayOf(PropTypes.shape({
    name:     PropTypes.string,
    count:    PropTypes.number,
    colorIdx: PropTypes.number,
  })).isRequired,
  total: PropTypes.number.isRequired,
};
