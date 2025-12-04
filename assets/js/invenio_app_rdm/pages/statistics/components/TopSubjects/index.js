/**
 * Top Subjects Component
 * Displays top research subjects with progress bars
 */

import React from "react";
import PropTypes from "prop-types";

export const TopSubjects = ({ data }) => {
  // UNESCO colors for subjects
  const unescoColors = ["#0077C8", "#00B398", "#ED2E7E", "#F39C12", "#9B59B6"];

  const maxCount = data.length > 0 ? data[0].count : 1;

  return (
    <div className="chart-card">
      <div className="chart-title">🏷️ Top Research Subjects</div>
      <div>
        {data.map((subject, index) => {
          const percentage = Math.round((subject.count / maxCount) * 100);
          const color = unescoColors[index % unescoColors.length];

          return (
            <div key={index} className="subject-item">
              <div className="subject-info">
                <div className="subject-name">{subject.name}</div>
                <div className="progress-bar-container">
                  <div
                    className="progress-bar"
                    style={{
                      width: `${percentage}%`,
                      background: color,
                    }}
                  />
                </div>
              </div>
              <div className="subject-count">
                {subject.count.toLocaleString()}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

TopSubjects.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      count: PropTypes.number.isRequired,
    })
  ).isRequired,
};
