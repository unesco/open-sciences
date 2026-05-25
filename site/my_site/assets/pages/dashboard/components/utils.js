/**
 * Dashboard Shared Utilities
 * Script/stylesheet loaders and colour helper.
 * Raw constants (palette, colors, CDN URL) live in ../constants.js.
 */

import React from "react";
import {
  BLUE_PALETTE,
  COLOR_YES,
  COLOR_NO,
  NA_LABEL,
  NA_LABEL_VARIANTS,
  NA_INFO_NOTE,
} from "../constants";
import {
  REGIONS,
  COLOR_NO_DATA,
  COLOR_BORDER,
  COLOR_PARTICIPATED,
  COLOR_MATCHES,
} from "./GlobalOverview/components/constants";

/**
 * Returns the chart segment colour for a given answer name and palette index.
 * "Yes" → brand blue, "No" → light grey, others → BLUE_PALETTE cycle.
 */
export function getAnswerColor(name, index) {
  const lower = (name || "").toLowerCase().trim();
  if (lower === "yes") return COLOR_YES;
  if (lower === "no")  return COLOR_NO;
  return BLUE_PALETTE[index % BLUE_PALETTE.length];
}

// ── Script / stylesheet loaders ──────────────────────────────────────────────

// Shared promises so concurrent callers all wait on the same load
const _scriptPromises = {};

export function loadScript(src, id) {
  if (_scriptPromises[id]) return _scriptPromises[id];
  _scriptPromises[id] = new Promise((resolve) => {
    const existing = document.getElementById(id);
    if (existing) {
      if (existing.readyState === "complete" || existing.readyState === "loaded") {
        resolve(); return;
      }
      existing.addEventListener("load", resolve, { once: true });
      // Fallback: poll window.Chart in case the load event already fired
      const poll = setInterval(() => {
        if (window.Chart) { clearInterval(poll); resolve(); }
      }, 50);
      return;
    }
    const s = document.createElement("script");
    s.src = src; s.id = id; s.async = true;
    s.onload = resolve;
    document.head.appendChild(s);
  });
  return _scriptPromises[id];
}

export function loadLink(href, id) {
  if (document.getElementById(id)) return;
  const l = document.createElement("link");
  l.rel = "stylesheet"; l.href = href; l.id = id;
  document.head.appendChild(l);
}

// ── HTML helpers ─────────────────────────────────────────────────────────────

export function decodeHtmlEntities(str) {
  if (!str) return "";
  return str
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"');
}

// ── Info-description helpers ───────────────────────────────────────────────

export function isNotApplicableLabel(label) {
  const l = (label || "").trim().toLowerCase();
  return NA_LABEL_VARIANTS.includes(l);
}

export function normaliseAnswerName(name) {
  return isNotApplicableLabel(name) ? NA_LABEL : (name || "").trim();
}

export function hasNotApplicableOption(options = []) {
  return (options || []).some((o) => isNotApplicableLabel(o && o.label));
}

export function buildInfoDescription(description, options = []) {
  const base = (description || "").trim();
  const appendNa = hasNotApplicableOption(options);
  if (base && appendNa) return `${base}\n\n${NA_INFO_NOTE}`;
  if (base) return base;
  if (appendNa) return NA_INFO_NOTE;
  return "";
}

// Render text with line breaks so tooltips and modals preserve the same output.
export function renderInfoDescription(description, options = []) {
  const text = buildInfoDescription(description, options);
  if (!text) return null;
  return text.split("\n").map((line, i) => (
    <React.Fragment key={`info-desc-line-${i}`}>
      {i > 0 && <br />}
      {line}
    </React.Fragment>
  ));
}

/**
 * Decode double-encoded HTML from Drupal's CKEditor storage.
 * Some fields arrive with entity-encoded tags like &lt;p&gt; inside a real <p>.
 * We decode iteratively so the browser renders actual HTML elements.
 */
export function sanitizeRichText(html) {
  if (!html || typeof html !== "string") return "";
  let decoded = html;
  let prev;
  do {
    prev = decoded;
    decoded = decoded
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&amp;((?:lt|gt|amp|quot|nbsp|apos);)/g, "&$1");
  } while (decoded !== prev);
  return decoded;
}

// ── Region helpers ──────────────────────────────────────────────────────────

/** Convert a display label to its API value. Returns the label itself as fallback. */
export function regionToApi(label) {
  const entry = REGIONS.find((r) => r.label === label);
  return entry && entry.apiValue ? entry.apiValue : label;
}

// Decode &amp; → & (iteratively for double-encoding) and lowercase for tolerant comparison.
export function normaliseRegion(s) {
  let r = (s || "").trim();
  while (r.includes("&amp;")) {
    r = r.replace(/&amp;/g, "&");
  }
  return r.toLowerCase();
}

// ── Survey-question helpers ─────────────────────────────────────────────────

// Parse a `closed_answer_options` string from the survey-questions API into
// an array of { code, label }. Format: "Y|Yes\nN|No\nP|Partly" — one option
// per line, code and label separated by `|`.
export function parseClosedAnswerOptions(raw) {
  if (!raw) return [];
  return raw
    .split(/\r?\n/)
    .map((line) => {
      const [code, ...labelParts] = line.split("|");
      const c = (code || "").trim();
      const label = labelParts.join("|").trim();
      return c ? { code: c, label: label || c } : null;
    })
    .filter(Boolean);
}

// Build the section/question filter tree from the API responses.
// Only "Closed" questions with a non-empty short_name and at least one
// parseable answer option are usable as filters; section "A" is the
// administrative section and is excluded.
export function buildFilterTree(sections, questions) {
  const usable = (questions || [])
    .filter((q) => q.type === "Closed" && q.short_name && q.short_name.trim())
    .map((q) => ({ ...q, _options: parseClosedAnswerOptions(q.closed_answer_options) }))
    .filter((q) => q._options.length > 0);
  return (sections || [])
    .filter((s) => s.id !== "A")
    .map((section) => ({
      id: `s${section.id}`,
      label: section.title,
      items: usable
        .filter((q) => q.section === section.id)
        .map((q) => ({
          id: `q${String(q.number).replace(/\./g, "_")}`,
          label: q.short_name.trim(),
          question: q.number,
          description: (q.long_description || q.description || "").trim(),
          options: q._options,
        })),
    }))
    .filter((g) => g.items.length > 0);
}

// ── Map helpers ─────────────────────────────────────────────────────────────

export function featureStyle(iso3, participatingSet, matchingSet) {
  if (matchingSet === null) {
    return {
      fillColor: COLOR_NO_DATA,
      fillOpacity: 1,
      color: COLOR_BORDER,
      weight: 0.7,
      opacity: 1,
    };
  }
  const isMatch       = matchingSet.has(iso3);
  const isParticipant = participatingSet.has(iso3);
  const fill = isMatch
    ? COLOR_MATCHES
    : isParticipant
    ? COLOR_PARTICIPATED
    : COLOR_NO_DATA;
  return {
    fillColor: fill,
    fillOpacity: 1,
    color: COLOR_BORDER,
    weight: 0.7,
    opacity: 1,
  };
}

// ── Shared icons ──────────────────────────────────────────────────────────────

/**
 * Medal / badge icon used in topic cards and country sidebar nav.
 * @param {string} className  CSS class applied to the <svg> element
 */
export const MedalIcon = ({ className }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    width="20"
    height="20"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="12" cy="14" r="6" fill="#1a6fa8" />
    <circle cx="12" cy="14" r="4" fill="white" />
    <circle cx="12" cy="14" r="2.5" fill="#1a6fa8" />
    <path d="M9 8.5L7 2h10l-2 6.5" stroke="#1a6fa8" strokeWidth="1.5" strokeLinejoin="round" fill="none" />
    <path d="M9 8.5 Q12 10 15 8.5" stroke="#1a6fa8" strokeWidth="1.5" fill="none" />
  </svg>
);
