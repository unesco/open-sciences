/**
 * CountryDetail Component
 * Full-page view for a single country's open science data.
 * Fetches rich-text content from the CMS countries endpoint.
 */

import React, { useState, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { fetchCountryByIso3 } from "../../api";
import { COUNTRY_SECTIONS } from "../../constants";
import { decodeHtmlEntities, sanitizeRichText, MedalIcon } from "../utils";

// ── CountryDetail component ─────────────────────────────────────────────────

export const CountryDetail = ({ iso3, countryName, onBack }) => {
  const [countryData, setCountryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const sectionRefs = useRef({});

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    fetchCountryByIso3(iso3)
      .then((data) => {
        if (!mounted) return;
        // API returns an array with one element
        const country = Array.isArray(data) ? data[0] : data;
        setCountryData(country || null);
      })
      .catch((err) => {
        if (!mounted) return;
        console.error("Failed to load country:", err);
        setError(err.message);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [iso3]);

  const scrollToSection = (sectionId) => {
    const el = sectionRefs.current[sectionId];
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const displayName =
    (countryData && countryData.name) || countryName || iso3;
  const regionDisplay =
    countryData && countryData.region
      ? decodeHtmlEntities(countryData.region)
      : "";

  // Filter sections that have content
  const activeSections = countryData
    ? COUNTRY_SECTIONS.filter((s) => {
        const val = countryData[s.field];
        return val && val.trim().length > 0;
      })
    : COUNTRY_SECTIONS;

  return (
    <div className="country-detail-page">
      {/* Back link */}
      <button type="button" className="country-back-link" onClick={onBack}>
        ← Go back to map
      </button>

      {/* Country header */}
      <div className="country-header-card">
        <div className="country-header-info">
          <h2 className="country-header-name">
            <img
              className="country-flag"
              src={`https://flagcdn.com/w40/${iso3.slice(0, 2).toLowerCase()}.png`}
              alt={`${displayName} flag`}
              onError={(e) => {
                e.target.style.display = "none";
              }}
            />
            {displayName}
          </h2>
          {/* {regionDisplay && (
            <span className="country-header-region">{regionDisplay}</span>
          )} */}
        </div>
        <a
          href={`/cms/api/countries/${encodeURIComponent(iso3)}/download`}
          className="country-download-btn"
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => {
            e.preventDefault();
            alert("Coming soon");
          }}
        >
          Download national submission ⬇
        </a>
      </div>

      {loading && (
        <div className="country-loading">Loading country data…</div>
      )}
      {error && (
        <div className="country-error">
          Failed to load country data: {error}
        </div>
      )}

      {!loading && !error && countryData && (
        <div className="country-content-layout">
          {/* Content sections — left */}
          <div className="country-content-main">
            {COUNTRY_SECTIONS.map((section) => {
              const raw = countryData[section.field];
              const html = raw ? sanitizeRichText(raw.trim()) : "";
              return (
                <div
                  key={section.id}
                  className="country-section"
                  ref={(el) => {
                    sectionRefs.current[section.id] = el;
                  }}
                >
                  <h3 className="country-section-title">{section.label}</h3>
                  {html ? (
                    <div
                      className="country-section-body"
                      dangerouslySetInnerHTML={{ __html: html }}
                    />
                  ) : (
                    <p className="country-section-empty">
                      No data available for this section.
                    </p>
                  )}
                </div>
              );
            })}
          </div>

          {/* On this page — sticky sidebar right */}
          <nav className="country-sidebar">
            <div className="country-sidebar-title">On this page:</div>
            <div className="country-sidebar-card">
              <ul className="country-sidebar-nav">
                {COUNTRY_SECTIONS.map((section) => (
                  <li key={section.id}>
                    <button
                      type="button"
                      className="country-sidebar-link"
                      onClick={() => scrollToSection(section.id)}
                    >
                      <MedalIcon className="country-section-icon" />
                      <span>{section.label}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </nav>
        </div>
      )}
    </div>
  );
};

CountryDetail.propTypes = {
  iso3: PropTypes.string.isRequired,
  countryName: PropTypes.string,
  onBack: PropTypes.func.isRequired,
};

CountryDetail.defaultProps = {
  countryName: undefined,
};
