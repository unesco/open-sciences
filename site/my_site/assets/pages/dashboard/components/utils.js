/**
 * Dashboard Shared Utilities
 * Helpers for dynamically loading external scripts and stylesheets
 */

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
