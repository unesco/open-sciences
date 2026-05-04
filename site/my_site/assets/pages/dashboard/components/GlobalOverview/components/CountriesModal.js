import React, { useState, useEffect, useMemo } from "react";
import { fetchCountries } from "../../../api";

export const CountriesModal = ({ onClose, onCountryClick }) => {
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchCountries()
      .then((data) => {
        const sorted = (data || [])
          .filter((c) => c.name && c.iso_3)
          .sort((a, b) => a.name.localeCompare(b.name));
        setCountries(sorted);
      })
      .catch((err) => console.error("[CountriesModal] fetch failed:", err))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    if (!searchTerm.trim()) return countries;
    const term = searchTerm.trim().toLowerCase();
    return countries.filter((c) => c.name.toLowerCase().includes(term));
  }, [countries, searchTerm]);

  const handleCountrySelect = (country) => {
    onClose();
    onCountryClick(country.iso_3, country.name);
  };

  return (
    <div
      className="disclaimer-overlay"
      role="presentation"
      onClick={onClose}
      onKeyDown={(e) => { if (e.key === "Escape") onClose(); }}
    >
      <div
        className="disclaimer-modal countries-modal"
        role="presentation"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
      >
        <div className="disclaimer-header">
          <h2 className="disclaimer-title">
            List of all countries that participated in the survey.
          </h2>
          <button
            type="button"
            className="disclaimer-close-x"
            onClick={onClose}
            aria-label="Close"
          >
            &times;
          </button>
        </div>

        <div className="countries-modal-body">
          <div className="countries-search-row">
            <input
              type="text"
              className="countries-search-input"
              placeholder="Search by country"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <button type="button" className="countries-search-btn">
              Search
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </button>
          </div>

          <p className="countries-count">
            All countries ({filtered.length})
          </p>

          {loading ? (
            <p className="countries-loading">Loading countries…</p>
          ) : filtered.length === 0 ? (
            <p className="countries-empty">No countries found.</p>
          ) : (
            <div className="countries-grid">
              {filtered.map((c) => (
                <button
                  key={c.iso_3}
                  type="button"
                  className="countries-grid-link"
                  onClick={() => handleCountrySelect(c)}
                >
                  {c.name}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="disclaimer-footer">
          <button type="button" className="disclaimer-close-btn" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
