/**
 * Shared info-icon component.
 * Renders the ⓘ + desktop hover tooltip + (optional) mobile modal.
 * Appends the N/A clarification when `options` contains an N/A entry.
 */

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { buildInfoDescription, renderInfoDescription } from "./utils";

export const InfoIcon = ({ description, options, modalTitle, ariaLabel = "Show question description" }) => {
  const [showInfo, setShowInfo] = useState(false);
  const text = buildInfoDescription(description, options);

  useEffect(() => {
    if (!showInfo) return;
    const onKey = (e) => e.key === "Escape" && setShowInfo(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [showInfo]);

  if (!text) return null;

  const handleClick = () => {
    if (typeof window !== "undefined" && window.matchMedia && window.matchMedia("(hover: none)").matches) {
      setShowInfo((v) => !v);
    }
  };

  return (
    <>
      <span className="info-icon-wrap">
        <span
          className="donut-info-icon"
          role="button"
          tabIndex={0}
          aria-label={ariaLabel}
          onClick={handleClick}
          onKeyDown={(e) => e.key === "Enter" && setShowInfo((v) => !v)}
        >
          <img src="/static/images/info_icn.png" alt="info" className="donut-info-icon-img" />
        </span>
        <span className="info-hover-tooltip" role="tooltip">
          {renderInfoDescription(description, options)}
        </span>
      </span>

      {showInfo && modalTitle && createPortal(
        <div
          className="donut-info-modal-backdrop"
          role="presentation"
          onClick={(e) => e.target === e.currentTarget && setShowInfo(false)}
        >
          <div role="dialog" aria-modal="true" aria-label={modalTitle} className="donut-info-modal">
            <div className="donut-info-modal-header">
              <span className="donut-info-modal-title">{modalTitle}</span>
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
              <p>{renderInfoDescription(description, options)}</p>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
};
