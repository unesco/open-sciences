// Choropleth colours
export const COLOR_NO_DATA      = "#D5DADD";
export const COLOR_BORDER       = "#ffffff";
export const COLOR_PARTICIPATED = "#4C5054";
export const COLOR_MATCHES      = "#B2D6F2";

// World GeoJSON — features use ISO Alpha-3 as `id`
export const WORLD_GEOJSON_URL =
  "https://cdn.jsdelivr.net/gh/johan/world.geo.json@master/countries.geo.json";

export const ALL_REGIONS = "All regions";

export const REGIONS = [
  { label: "All regions",                    apiValue: null,                             view: null },
  { label: "Africa",                         apiValue: "Africa",                         view: { center: [5,    20],  zoom: 2.5 } },
  { label: "Arab States",                    apiValue: "Arab States",                    view: { center: [25,   42],  zoom: 3.5 } },
  { label: "Asia-Pacific",                   apiValue: "Asia & the Pacific",             view: { center: [25,   100], zoom: 2.5 } },
  { label: "Europe & North America",         apiValue: "Europe & North America",         view: { center: [50,   -20], zoom: 3 } },
  { label: "Latin America & the Caribbean",  apiValue: "Latin America & the Caribbean",  view: { center: [-15,  -60], zoom: 2.5 } },
];

// Derived lookups for convenience — kept for backward-compat with existing consumers.
export const REGION_LABELS = REGIONS.map((r) => r.label);

export const REGION_DISPLAY_TO_API = Object.fromEntries(
  REGIONS.filter((r) => r.apiValue).map((r) => [r.label, r.apiValue])
);

export const REGION_VIEW = Object.fromEntries(
  REGIONS.filter((r) => r.view).map((r) => [r.label, r.view])
);

/** Convert a display label to its API value. Returns the label itself as fallback. */
export function regionToApi(label) {
  const entry = REGIONS.find((r) => r.label === label);
  return entry && entry.apiValue ? entry.apiValue : label;
}

// Decode &amp; → & (iteratively for double-encoding) and lowercase for tolerant comparison.
export function normaliseRegion(s) {
  let r = (s || "").trim();
  // Iteratively decode &amp; to handle single or double encoding.
  while (r.includes("&amp;")) {
    r = r.replace(/&amp;/g, "&");
  }
  return r.toLowerCase();
}

// Build the section/question filter tree from the API responses.
// Only "Closed" questions with a non-empty short_name are usable as Yes/No
// filters; section "A" is the administrative section and is excluded.
export function buildFilterTree(sections, questions) {
  const usable = (questions || []).filter(
    (q) => q.type === "Closed" && q.short_name && q.short_name.trim()
  );
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
        })),
    }))
    .filter((g) => g.items.length > 0);
}

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
