/**
 * Dashboard Shared Utilities
 * Script/stylesheet loaders and colour helper.
 * All raw constants (palette, colors, regions, CDN URL) live in ../constants.js.
 */

import React from "react";
import {
  BLUE_PALETTE,
  COLOR_YES,
  COLOR_NO,
  COLOR_PARTLY,
  COLOR_UNDER_DEVELOPMENT,
  COLOR_NA_ANSWER,
  NA_LABEL,
  NA_LABEL_VARIANTS,
  NA_INFO_NOTE,
} from "../constants";
import {
  REGIONS,
  REGION_COLORS,
  COLOR_NO_DATA,
  COLOR_BORDER,
  COLOR_PARTICIPATED,
  COLOR_MATCHES,
} from "../constants";

// Fixed colour per standard closed-answer option (lower-cased label → colour).
// Shared by every comparison chart so Yes/No/Partly/etc. read the same
// everywhere (donuts, region & country breakdowns, mini donuts, legends).
const ANSWER_COLORS = {
  "yes": COLOR_YES,
  "no": COLOR_NO,
  "partly": COLOR_PARTLY,
  "under development": COLOR_UNDER_DEVELOPMENT,
};

/**
 * Returns the chart segment colour for a given answer name and palette index.
 * Standard options (Yes/No/Partly/Under Development) and N/A use their fixed
 * brand colours; any other answer falls back to the BLUE_PALETTE cycle.
 */
export function getAnswerColor(name, index) {
  if (isNotApplicableLabel(name)) return COLOR_NA_ANSWER;
  const lower = (name || "").toLowerCase().trim();
  if (ANSWER_COLORS[lower]) return ANSWER_COLORS[lower];
  return BLUE_PALETTE[index % BLUE_PALETTE.length];
}

/**
 * Returns the fixed chart colour for a region name so the same region always
 * reads as the same shade regardless of segment order. Unknown regions fall
 * back to the BLUE_PALETTE cycle.
 */
export function getRegionColor(name, index) {
  const key = normaliseRegion(name);
  if (REGION_COLORS[key]) return REGION_COLORS[key];
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
  // Strip empty paragraphs that CKEditor often inserts for spacing.
  decoded = decoded.replace(/<p>(?:\s|&nbsp;)*<\/p>/gi, "");
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

// ── Sub-question breakdown helpers ──────────────────────────────────────────

/**
 * Parse a sub-question's long_description into { intro, bullets }.
 * Stored format (from CMS):
 *   "Intro text…: - first bullet; - second bullet; - third bullet"
 * Returns null when no dash-separated bullets are detected.
 */
export function parseSubDetailsDescription(raw) {
  if (!raw) return null;
  const text = decodeHtmlEntities(String(raw)).replace(/\s+/g, " ").trim();
  if (!text) return null;
  // Split on " - " (the bullet separator used in the source data).
  const parts = text.split(/\s+-\s+/);
  if (parts.length < 2) return null;
  const intro = parts[0].replace(/\s+$/, "");
  const bullets = parts
    .slice(1)
    .map((b) => b.replace(/^[-\s]+/, "").replace(/[;,\s]+$/, "").trim())
    .filter(Boolean);
  if (bullets.length === 0) return null;
  return { intro, bullets };
}

/**
 * Build the sub-details payload to render in the breakdown drawer for a
 * parent question (e.g. Q 3.4). Returns { intro, items: [{ count, text }] }
 * or null when the question has no sub-question data to surface.
 *
 * Two layouts are supported:
 *  1. One closed sub-question per bullet (Q 3.4 has 3.4.1..3.4.4).
 *     count = number of "Y"/"Yes" responses to that sub-question.
 *  2. Single closed sub-question with multiple answer-value bullets
 *     (Q 3.5 has 3.5.2 with "Yes, accessible" / "No, not accessible").
 *     count = number of responses for each ordered answer value.
 */
export function buildSubDetails(parentQuestion, allQuestions, responsesMap) {
  if (!parentQuestion || !parentQuestion.number) return null;
  const prefix = `${parentQuestion.number}.`;
  const subQs = (allQuestions || [])
    .filter((q) => q.type === "Closed" && q.number && q.number.startsWith(prefix))
    .sort((a, b) => String(a.number).localeCompare(String(b.number), undefined, { numeric: true }));
  if (subQs.length === 0) return null;

  const introHolder = subQs.find((q) => q.long_description);
  if (!introHolder) return null;
  const parsed = parseSubDetailsDescription(introHolder.long_description);
  if (!parsed) return null;

  const isYesKey = (k) => /^(y|yes)$/i.test((k || "").trim());

  let items = null;
  if (subQs.length === parsed.bullets.length) {
    items = parsed.bullets.map((text, i) => {
      const stats = responsesMap[subQs[i].number] || { answers: {} };
      const count = Object.entries(stats.answers || {})
        .filter(([k]) => isYesKey(k))
        .reduce((s, [, v]) => s + v, 0);
      return { count, text };
    });
  } else if (subQs.length === 1) {
    const stats = responsesMap[subQs[0].number] || { answers: {} };
    const answers = stats.answers || {};
    const orderedKeys = Object.keys(answers)
      .filter((k) => !isNotApplicableLabel(k))
      .sort((a, b) => (isYesKey(b) ? 1 : 0) - (isYesKey(a) ? 1 : 0));
    items = parsed.bullets.map((text, i) => ({
      count: answers[orderedKeys[i]] || 0,
      text,
    }));
  } else {
    return null;
  }

  return { intro: parsed.intro, items };
}

/**
 * Return the list of sub-question numbers that will be folded into a parent
 * question's breakdown sub-section, or null if no sub-section will render.
 *
 * Mirrors the structural rules in `buildSubDetails` (one-bullet-per-sub-question
 * or single-sub-question with answer-value bullets) but ignores response data,
 * since the fold decision is purely structural. Used by the donut grid to hide
 * sub-question cards whose data is already surfaced inside the parent drawer.
 */
export function subQuestionsFoldedIntoParent(parentQuestion, allQuestions) {
  if (!parentQuestion || !parentQuestion.number) return null;
  const prefix = `${parentQuestion.number}.`;
  const subQs = (allQuestions || [])
    .filter((q) => q.type === "Closed" && q.number && q.number.startsWith(prefix))
    .sort((a, b) => String(a.number).localeCompare(String(b.number), undefined, { numeric: true }));
  if (subQs.length === 0) return null;
  const introHolder = subQs.find((q) => q.long_description);
  if (!introHolder) return null;
  const parsed = parseSubDetailsDescription(introHolder.long_description);
  if (!parsed) return null;
  if (subQs.length === parsed.bullets.length || subQs.length === 1) {
    return subQs.map((q) => q.number);
  }
  return null;
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

  // Sub-questions whose data is folded into a parent question's breakdown
  // (via long_description) should not also appear as standalone filter items —
  // they only surface in the country report. Mirrors the Comparison dashboard.
  const hiddenSubQuestionNumbers = new Set(
    (questions || []).flatMap((q) => subQuestionsFoldedIntoParent(q, questions) || [])
  );

  return (sections || [])
    .filter((s) => s.id !== "A")
    .map((section) => ({
      id: `s${section.id}`,
      label: section.title,
      items: usable
        .filter((q) => q.section === section.id && !hiddenSubQuestionNumbers.has(q.number))
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
    viewBox="0 0 32 32"
    width="32"
    height="32"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="16" cy="16" r="16" fill="#0077d4" />
    <path
      d="M10 12h12M10 16h12M10 20h8"
      stroke="#ffffff"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
);
