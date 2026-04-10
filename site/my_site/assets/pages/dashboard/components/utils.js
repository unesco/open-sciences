/**
 * Dashboard Shared Utilities
 * Script/stylesheet loaders and colour helper.
 * Raw constants (palette, colors, CDN URL) live in ../constants.js.
 */

import React from "react";
import { BLUE_PALETTE, COLOR_YES, COLOR_NO } from "../constants";

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
