/**
 * CountryBreakdownModal Component
 * Slide-in drawer showing per-country Yes / Partial / No breakdown for a survey question
 */

import React, { useEffect } from "react";
import PropTypes from "prop-types";

// ─── Data ──────────────────────────────────────────────────────────────────

export const COUNTRY_BREAKDOWN = {
  // t1 – q0: UNESCO Recommendation on Open Science formally promoted
  "t1-0": {
    yes: {
      count: 55, pct: 70,
      countries: ["Albania","Algeria","Angola","Australia","Belgium","Botswana","Brazil","Bulgaria",
        "Canada","Chile","Colombia","Croatia","Cyprus","Czechia","Denmark","Ecuador",
        "Estonia","Ethiopia","Finland","France","Georgia","Germany","Ghana","Greece",
        "Hungary","India","Indonesia","Ireland","Italy","Japan","Jordan","Kazakhstan",
        "Kenya","Latvia","Lithuania","Malaysia","Mexico","Morocco","Netherlands",
        "New Zealand","Nigeria","North Macedonia","Norway","Pakistan","Peru","Philippines",
        "Poland","Portugal","Romania","Rwanda","Serbia","Slovakia","Slovenia","Spain","Sweden"],
      subDetails: null,
    },
    partial: {
      count: 4, pct: 5,
      countries: ["Armenia","Azerbaijan","Bolivia","Cameroon"],
      subDetails: null,
    },
    no: {
      count: 22, pct: 25,
      countries: ["Bangladesh","Côte d'Ivoire","Paraguay","Pakistan","Oman","Senegal",
        "Sri Lanka","Thailand","Tunisia","Ukraine","Uzbekistan","Vietnam"],
      subDetails: null,
    },
  },
  // t1 – q1: Awareness-raising activities on open science
  "t1-1": {
    yes: {
      count: 55, pct: 70,
      countries: ["Albania","Algeria","Angola","Australia","Belgium","Botswana","Brazil","Bulgaria",
        "Canada","Chile","Colombia","Croatia","Czechia","Denmark","Ecuador","Estonia",
        "Finland","France","Georgia","Ghana","Greece","Hungary","India","Indonesia",
        "Ireland","Italy","Japan","Kazakhstan","Kenya","Latvia","Malaysia","Mexico",
        "Morocco","Netherlands","New Zealand","Nigeria","North Macedonia","Norway",
        "Peru","Philippines","Poland","Portugal","Romania","Serbia","Slovakia","Slovenia",
        "Spain","Sweden","Tunisia","Ukraine","Uzbekistan","Vietnam","Cameroon","Ethiopia","Jordan"],
      subDetails: null,
    },
    partial: { count: 4, pct: 5, countries: ["Armenia","Azerbaijan","Bolivia","Pakistan"], subDetails: null },
    no: { count: 22, pct: 25,
      countries: ["Bangladesh","Côte d'Ivoire","Paraguay","Oman","Senegal","Sri Lanka","Thailand"],
      subDetails: null },
  },
  // t2 – q0: National open science policy adopted
  "t2-0": {
    yes: { count: 42, pct: 52,
      countries: ["Albania","Algeria","Australia","Belgium","Brazil","Canada","Chile","Colombia",
        "Croatia","Czechia","Denmark","Estonia","Finland","France","Georgia","Germany",
        "Ghana","Greece","Hungary","India","Indonesia","Ireland","Italy","Japan","Kazakhstan",
        "Kenya","Latvia","Malaysia","Mexico","Morocco","Netherlands","New Zealand","Nigeria",
        "North Macedonia","Norway","Poland","Portugal","Romania","Serbia","Slovakia","Slovenia","Spain"],
      subDetails: null },
    partial: { count: 8, pct: 10, countries: ["Armenia","Azerbaijan","Bolivia","Botswana","Bulgaria","Cameroon","Ecuador","Ethiopia"], subDetails: null },
    no: { count: 31, pct: 38,
      countries: ["Angola","Bangladesh","Chile","Côte d'Ivoire","Paraguay","Pakistan","Oman",
        "Peru","Philippines","Rwanda","Senegal","Sri Lanka","Sweden","Thailand","Tunisia",
        "Ukraine","Uzbekistan","Vietnam"],
      subDetails: null },
  },
  // t2 – q1: Open science action plan in place
  "t2-1": {
    yes: { count: 38, pct: 47,
      countries: ["Australia","Belgium","Brazil","Canada","Colombia","Croatia","Czechia",
        "Denmark","Estonia","Finland","France","Germany","Ghana","Hungary","India",
        "Ireland","Italy","Japan","Kazakhstan","Latvia","Mexico","Morocco","Netherlands",
        "New Zealand","Nigeria","Norway","Poland","Portugal","Romania","Serbia","Slovakia",
        "Slovenia","Spain","Sweden","Tunisia","Ukraine","Uzbekistan","Vietnam"],
      subDetails: null },
    partial: { count: 5, pct: 6, countries: ["Albania","Algeria","Angola","Armenia","Azerbaijan"], subDetails: null },
    no: { count: 38, pct: 47,
      countries: ["Bangladesh","Bolivia","Botswana","Bulgaria","Cameroon","Chile","Colombia",
        "Côte d'Ivoire","Ecuador","Ethiopia","Georgia","Greece","Hungary","Indonesia",
        "Jordan","Kenya","Malaysia"],
      subDetails: null },
  },
  // t3 – q0: National open access repository operational
  "t3-0": {
    yes: {
      count: 50, pct: 62,
      countries: ["Albania","Algeria","Angola","Botswana","Finland","Ireland","Japan",
        "North Macedonia","Serbia","Slovakia","Slovenia","Australia","Belgium","Brazil",
        "Canada","Chile","Colombia","Croatia","Czechia","Denmark","Estonia","France",
        "Georgia","Germany","Ghana","Greece","Hungary","India","Indonesia","Italy",
        "Kazakhstan","Kenya","Latvia","Malaysia","Mexico","Morocco","Netherlands",
        "New Zealand","Nigeria","Norway","Philippines","Poland","Portugal","Romania",
        "Spain","Sweden","Tunisia","Ukraine","Uzbekistan","Vietnam"],
      subDetails: [
        { count: 30, text: "Federated information technology infrastructure for open science, including high-performance computing, cloud computing and data storage" },
        { count: 23, text: "Community managed infrastructures, protocols and standards, for example those that support bibliodiversity and engagement with society" },
        { count: 13, text: "Platforms for exchanges and co-creation of knowledge between scientists and society" },
        { count: 13, text: "Community-based monitoring and information systems to complement national, regional and global data and information systems" },
      ],
    },
    partial: { count: 4, pct: 5, countries: ["Germany","Malaysia","North Macedonia","Peru"], subDetails: null },
    no: { count: 27, pct: 33,
      countries: ["Armenia","Azerbaijan","Bangladesh","Bolivia","Bulgaria","Cameroon",
        "Côte d'Ivoire","Ecuador","Ethiopia","Jordan","Oman","Pakistan","Paraguay",
        "Peru","Rwanda","Senegal","Sri Lanka","Thailand"],
      subDetails: null },
  },
  // t3 – q1: Open data infrastructure investment
  "t3-1": {
    yes: { count: 45, pct: 56,
      countries: ["Albania","Algeria","Australia","Belgium","Brazil","Canada","Chile","Colombia",
        "Croatia","Czechia","Denmark","Estonia","Finland","France","Georgia","Germany",
        "Ghana","Greece","Hungary","India","Indonesia","Ireland","Italy","Japan","Kazakhstan",
        "Kenya","Latvia","Malaysia","Mexico","Morocco","Netherlands","New Zealand","Nigeria",
        "North Macedonia","Norway","Poland","Portugal","Romania","Serbia","Slovakia",
        "Slovenia","Spain","Sweden","Ukraine"],
      subDetails: null },
    partial: { count: 5, pct: 6, countries: ["Angola","Armenia","Azerbaijan","Bolivia","Botswana"], subDetails: null },
    no: { count: 31, pct: 38,
      countries: ["Bangladesh","Bulgaria","Cameroon","Chile","Côte d'Ivoire","Ecuador",
        "Ethiopia","Jordan","Oman","Pakistan","Paraguay","Peru","Philippines","Rwanda",
        "Senegal","Sri Lanka","Thailand","Tunisia","Ukraine","Uzbekistan","Vietnam"],
      subDetails: null },
  },
  // t4 – q0: Open science training programmes available
  "t4-0": {
    yes: { count: 47, pct: 58,
      countries: ["Albania","Algeria","Australia","Belgium","Brazil","Canada","Colombia",
        "Croatia","Czechia","Denmark","Estonia","Finland","France","Georgia","Germany",
        "Ghana","Greece","Hungary","India","Indonesia","Ireland","Italy","Japan","Kazakhstan",
        "Kenya","Latvia","Malaysia","Mexico","Morocco","Netherlands","New Zealand","Nigeria",
        "North Macedonia","Norway","Philippines","Poland","Portugal","Romania","Serbia",
        "Slovakia","Slovenia","Spain","Sweden","Tunisia","Ukraine","Uzbekistan","Vietnam"],
      subDetails: null },
    partial: { count: 6, pct: 7, countries: ["Angola","Armenia","Azerbaijan","Bolivia","Botswana","Bulgaria"], subDetails: null },
    no: { count: 28, pct: 35,
      countries: ["Bangladesh","Cameroon","Chile","Côte d'Ivoire","Ecuador","Ethiopia",
        "Jordan","Oman","Pakistan","Paraguay","Peru","Rwanda","Senegal","Sri Lanka","Thailand"],
      subDetails: null },
  },
  // t4 – q1: Digital literacy initiatives funded
  "t4-1": {
    yes: { count: 39, pct: 48,
      countries: ["Albania","Australia","Belgium","Brazil","Canada","Colombia","Croatia",
        "Czechia","Denmark","Estonia","Finland","France","Georgia","Germany","Ghana",
        "Greece","Hungary","India","Indonesia","Ireland","Italy","Japan","Kazakhstan",
        "Kenya","Latvia","Malaysia","Mexico","Morocco","Netherlands","New Zealand","Nigeria",
        "Norway","Poland","Portugal","Romania","Serbia","Slovakia","Slovenia","Spain"],
      subDetails: null },
    partial: { count: 7, pct: 9, countries: ["Algeria","Angola","Armenia","Azerbaijan","Bolivia","Botswana","Bulgaria"], subDetails: null },
    no: { count: 35, pct: 43,
      countries: ["Bangladesh","Cameroon","Chile","Côte d'Ivoire","Ecuador","Ethiopia",
        "Jordan","North Macedonia","Oman","Pakistan","Paraguay","Peru","Philippines",
        "Rwanda","Senegal","Sri Lanka","Sweden","Thailand","Tunisia","Ukraine","Uzbekistan","Vietnam"],
      subDetails: null },
  },
  // t5 – q0: Incentives for open publishing
  "t5-0": {
    yes: { count: 33, pct: 41,
      countries: ["Albania","Australia","Belgium","Brazil","Canada","Czechia","Denmark",
        "Estonia","Finland","France","Germany","Ghana","Greece","Hungary","India",
        "Indonesia","Ireland","Italy","Japan","Kazakhstan","Latvia","Mexico","Morocco",
        "Netherlands","New Zealand","Nigeria","Norway","Poland","Portugal","Romania","Serbia","Slovakia","Slovenia"],
      subDetails: null },
    partial: { count: 7, pct: 9, countries: ["Algeria","Angola","Armenia","Azerbaijan","Bolivia","Botswana","Bulgaria"], subDetails: null },
    no: { count: 41, pct: 50,
      countries: ["Bangladesh","Cameroon","Chile","Colombia","Croatia","Côte d'Ivoire",
        "Ecuador","Ethiopia","Georgia","Jordan","Kenya","Latvia","Malaysia",
        "North Macedonia","Oman","Pakistan","Paraguay","Peru","Philippines","Rwanda",
        "Senegal","Spain","Sri Lanka","Sweden","Thailand","Tunisia","Ukraine","Uzbekistan","Vietnam"],
      subDetails: null },
  },
  // t5 – q1: Open science culture promoted
  "t5-1": {
    yes: { count: 52, pct: 64,
      countries: ["Albania","Algeria","Angola","Australia","Belgium","Bolivia","Botswana",
        "Brazil","Bulgaria","Canada","Chile","Colombia","Croatia","Czechia","Denmark",
        "Estonia","Finland","France","Georgia","Germany","Ghana","Greece","Hungary","India",
        "Indonesia","Ireland","Italy","Japan","Kazakhstan","Kenya","Latvia","Malaysia",
        "Mexico","Morocco","Netherlands","New Zealand","Nigeria","North Macedonia","Norway",
        "Philippines","Poland","Portugal","Romania","Serbia","Slovakia","Slovenia","Spain","Sweden","Tunisia","Ukraine","Uzbekistan","Vietnam"],
      subDetails: null },
    partial: { count: 4, pct: 5, countries: ["Armenia","Azerbaijan","Bangladesh","Cameroon"], subDetails: null },
    no: { count: 25, pct: 31,
      countries: ["Côte d'Ivoire","Ecuador","Ethiopia","Jordan","Oman","Pakistan",
        "Paraguay","Peru","Rwanda","Senegal","Sri Lanka","Thailand"],
      subDetails: null },
  },
  // t6 – q0: Citizen science initiatives
  "t6-0": {
    yes: { count: 29, pct: 36,
      countries: ["Australia","Belgium","Brazil","Canada","Czechia","Denmark","Estonia",
        "Finland","France","Germany","Greece","Hungary","Ireland","Italy","Japan",
        "Kazakhstan","Mexico","Morocco","Netherlands","New Zealand","Norway","Poland",
        "Portugal","Romania","Serbia","Slovakia","Slovenia","Spain","Sweden"],
      subDetails: null },
    partial: { count: 7, pct: 9, countries: ["Albania","Algeria","Angola","Armenia","Azerbaijan","Bolivia","Botswana"], subDetails: null },
    no: { count: 45, pct: 55,
      countries: ["Bangladesh","Bulgaria","Cameroon","Chile","Colombia","Croatia","Côte d'Ivoire",
        "Ecuador","Ethiopia","Georgia","Ghana","Hungary","India","Indonesia","Jordan",
        "Kenya","Latvia","Malaysia","Nigeria","North Macedonia","Oman","Pakistan",
        "Paraguay","Peru","Philippines","Rwanda","Senegal","Sri Lanka","Thailand",
        "Tunisia","Ukraine","Uzbekistan","Vietnam"],
      subDetails: null },
  },
  // t6 – q1: Open innovation frameworks
  "t6-1": {
    yes: { count: 36, pct: 44,
      countries: ["Albania","Australia","Belgium","Brazil","Canada","Colombia","Czechia",
        "Denmark","Estonia","Finland","France","Germany","Greece","Hungary","India",
        "Ireland","Italy","Japan","Kazakhstan","Latvia","Mexico","Morocco","Netherlands",
        "New Zealand","Norway","Poland","Portugal","Romania","Serbia","Slovakia","Slovenia",
        "Spain","Sweden","Tunisia","Ukraine","Vietnam"],
      subDetails: null },
    partial: { count: 6, pct: 7, countries: ["Algeria","Angola","Armenia","Azerbaijan","Bolivia","Botswana"], subDetails: null },
    no: { count: 39, pct: 49,
      countries: ["Bangladesh","Bulgaria","Cameroon","Chile","Côte d'Ivoire","Croatia",
        "Ecuador","Ethiopia","Georgia","Ghana","Indonesia","Jordan","Kenya","Malaysia",
        "Nigeria","North Macedonia","Oman","Pakistan","Paraguay","Peru","Philippines",
        "Rwanda","Senegal","Sri Lanka","Thailand","Ukraine","Uzbekistan"],
      subDetails: null },
  },
};

// ─── Section colour config ─────────────────────────────────────────────────

const SECTION_COLORS = {
  yes:     { dot: "#0073b7", label: "Yes" },
  partial: { dot: "#f0a500", label: "Partial" },
  no:      { dot: "#555",    label: "No" },
};

// ─── Component ─────────────────────────────────────────────────────────────

export const CountryBreakdownModal = ({ chartLabel, breakdownKey, onClose }) => {
  const data = COUNTRY_BREAKDOWN[breakdownKey];

  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  if (!data) return null;

  const sections = [
    { key: "yes",     ...data.yes,     ...SECTION_COLORS.yes },
    ...(data.partial ? [{ key: "partial", ...data.partial, ...SECTION_COLORS.partial }] : []),
    { key: "no",      ...data.no,      ...SECTION_COLORS.no },
  ];

  return (
    <>
      {/* Backdrop */}
      <div
        className="breakdown-backdrop"
        role="button"
        tabIndex={0}
        aria-label="Close breakdown"
        onClick={onClose}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onClose(); }}
      />

      {/* Drawer panel */}
      <div className="breakdown-drawer" role="dialog" aria-modal="true" aria-label="Country breakdown">
        <div className="breakdown-header">
          <h3 className="breakdown-title">
            {chartLabel}
            <span className="breakdown-info-icon" title="Survey question">ⓘ</span>
          </h3>
          <button type="button" className="breakdown-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="breakdown-body">
          {sections.map((section) => (
            <div key={section.key} className="breakdown-section">
              <div className="breakdown-section-heading">
                <span className="breakdown-dot" style={{ background: section.dot }} />
                <span className="breakdown-section-label">
                  {section.label}, {section.pct}%
                  {section.count != null && (
                    <span className="breakdown-section-count"> ({section.count} responses)</span>
                  )}
                </span>
              </div>

              {section.countries && section.countries.length > 0 && (
                <div className="breakdown-country-grid">
                  {section.countries.map((c) => (
                    <button key={c} type="button" className="breakdown-country-link">
                      {c}
                    </button>
                  ))}
                </div>
              )}

              {section.subDetails && section.subDetails.length > 0 && (
                <div className="breakdown-subdetails">
                  <p className="breakdown-subdetails-intro">
                    Countries selecting &#8216;yes&#8217; or &#8216;under development&#8217; reported additional
                    details on the availability of the following types of open science infrastructure:
                  </p>
                  {section.subDetails.map((d, i) => (
                    <div key={i} className="breakdown-subdetail-row">
                      <span className="breakdown-subdetail-badge">{d.count} responses</span>
                      <span className="breakdown-subdetail-text">{d.text}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

CountryBreakdownModal.propTypes = {
  chartLabel: PropTypes.string.isRequired,
  breakdownKey: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};
