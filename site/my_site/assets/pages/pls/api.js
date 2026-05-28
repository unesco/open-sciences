/**
 * PLS detail API helper.
 * Fetches a single Plain Language Summary from the Drupal-backed endpoint.
 */

const isDev =
  (window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1") &&
  window.location.port !== "" &&
  window.location.port !== "80" &&
  window.location.port !== "443";

const CMS_BASE = isDev ? "http://localhost:8080/cms" : "/cms";
const CMS_ORIGIN = isDev ? "http://localhost:8080" : "";

/**
 * Resolve a CMS-relative asset path (logos, SDG icons, etc.) returned by
 * the Drupal API into an absolute URL that works in both dev and prod.
 *
 * - "/sites/default/files/foo.png"  → "http://localhost:8080/sites/default/files/foo.png" (dev)
 *                                     "/cms/sites/default/files/foo.png" (prod)
 * - "/cms/sites/default/files/..."  → "http://localhost:8080/cms/..." (dev) | as-is (prod)
 * - "http(s)://..."                 → unchanged
 * - falsy                           → ""
 */
export function resolveCmsAsset(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith("/cms/")) return CMS_ORIGIN + path;
  if (path.startsWith("/")) return (isDev ? CMS_ORIGIN : "/cms") + path;
  return path;
}

export async function fetchPlsDetail(nid) {
  const response = await fetch(`${CMS_BASE}/api/pls/${encodeURIComponent(nid)}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });

  if (response.status === 404) {
    const err = new Error("Not found");
    err.status = 404;
    throw err;
  }
  if (!response.ok) {
    throw new Error(`GET /api/pls/${nid} failed: ${response.status}`);
  }
  return response.json();
}
