/**
 * WordCloud React Component
 * Renders words using spiral-based absolute positioning.
 * Scales font sizes down to fit within the available container width.
 */

import React, { useMemo, useRef, useState, useEffect, useCallback } from "react";
import { computeLayout } from "./wordCloudLayout";

export const WordCloud = ({ words, loading = false, minFontSize = 13, maxFontSize = 56, onWordClick }) => {
  const wrapperRef = useRef(null);
  const [availableWidth, setAvailableWidth] = useState(0);

  const measure = useCallback(() => {
    if (wrapperRef.current) {
      const padding = 80; // 40px left + 40px right from wrapper padding
      setAvailableWidth(wrapperRef.current.clientWidth - padding);
    }
  }, []);

  useEffect(() => {
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [measure]);

  // Compute layout, scaling font sizes to fit available width
  const { placed, cloudWidth, cloudHeight } = useMemo(() => {
    if (!words.length) return { placed: [], cloudWidth: 0, cloudHeight: 0 };

    // First pass at full size
    const full = computeLayout(words, minFontSize, maxFontSize);

    if (availableWidth <= 0 || full.cloudWidth <= availableWidth) {
      return full;
    }

    // Scale font sizes down proportionally to fit
    const scale = availableWidth / full.cloudWidth;
    return computeLayout(words, minFontSize * scale, maxFontSize * scale);
  }, [words, minFontSize, maxFontSize, availableWidth]);

  const handleClick = (item) => {
    if (onWordClick) {
      const word = words.find((w) => w.text === item.text);
      onWordClick(word || { text: item.text, count: 0 });
    }
  };

  return (
    <div className="word-cloud-wrapper" ref={wrapperRef}>
      {loading || !placed.length ? (
        <div className="word-cloud-loader">
          <span className="word-cloud-spinner" />
        </div>
      ) : (
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
      )}
    </div>
  );
};
