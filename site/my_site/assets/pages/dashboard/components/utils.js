/**
 * Dashboard Shared Utilities
 * Script/stylesheet loaders and colour helper.
 * Raw constants (palette, colors, CDN URL) live in ../constants.js.
 */

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
