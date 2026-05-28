import React from "react";

export const NoDataModal = ({ onClose }) => (
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
        <h2 className="disclaimer-title">Countries without data</h2>
        <button type="button" className="disclaimer-close-x" onClick={onClose} aria-label="Close">
          &times;
        </button>
      </div>
      <div className="disclaimer-body">
        <p>
          Countries shown in light grey did not participate in the 2025 reporting on the implementation of the UNESCO Recommendation on Open Science.
        </p>
        <p>
          Contact your{" "}
          <a
            href="https://pax.unesco.org/countries/NationalCommissions.html"
            target="_blank"
            rel="noopener noreferrer"
          >
            UNESCO National Commission
          </a>{" "}
          to explore participation in the 2029 reporting cycle.
        </p>
      </div>
      <div className="disclaimer-footer">
        <button type="button" className="disclaimer-close-btn" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  </div>
);
