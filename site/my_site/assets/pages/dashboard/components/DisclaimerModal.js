import React from "react";
import { DISCLAIMER_TEXT } from "../constants";

export const DisclaimerModal = ({ onClose }) => (
  <div
    className="disclaimer-overlay"
    role="presentation"
    onClick={onClose}
    onKeyDown={(e) => { if (e.key === "Escape") onClose(); }}
  >
    <div
      className="disclaimer-modal"
      role="presentation"
      onClick={(e) => e.stopPropagation()}
      onKeyDown={(e) => e.stopPropagation()}
    >
      <div className="disclaimer-header">
        <h2 className="disclaimer-title">UNESCO Disclaimer</h2>
        <button type="button" className="disclaimer-close-x" onClick={onClose} aria-label="Close">
          &times;
        </button>
      </div>
      <div className="disclaimer-body">
        <p>{DISCLAIMER_TEXT}</p>
      </div>
      <div className="disclaimer-footer">
        <button type="button" className="disclaimer-close-btn" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  </div>
);
