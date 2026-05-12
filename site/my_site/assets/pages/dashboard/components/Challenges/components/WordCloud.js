/**
 * WordCloud React Component
 * Renders words using spiral-based absolute positioning.
 */

import React, { useMemo } from "react";
import { computeLayout } from "./wordCloudLayout";

export const WordCloud = ({ words, minFontSize = 13, maxFontSize = 56, onWordClick }) => {
  const { placed, cloudWidth, cloudHeight } = useMemo(
    () => computeLayout(words, minFontSize, maxFontSize),
    [words, minFontSize, maxFontSize]
  );

  if (!words.length) return null;

  const handleClick = (item) => {
    if (onWordClick) {
      const word = words.find((w) => w.text === item.text);
      onWordClick(word || { text: item.text, count: 0 });
    }
  };

  return (
    <div className="word-cloud-wrapper">
      <div
        className="word-cloud-container"
        style={{ width: cloudWidth, height: cloudHeight }}
      >
        {placed.map((item) => (
          <span
            key={item.text}
            className="word-cloud-item"
            role="button"
            tabIndex={0}
            onClick={() => handleClick(item)}
            onKeyDown={(e) => e.key === "Enter" && handleClick(item)}
            style={{
              position: "absolute",
              left: item.x,
              top: item.y,
              fontSize: item.fontSize,
            }}
          >
            {item.text}
          </span>
        ))}
      </div>
    </div>
  );
};
