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
  ALL_REGIONS,
  "Africa",
  "Arab States",
  "Asia-Pacific",
  "Europe",
  "Latin America & the Caribbean",
  "North America",
];

// Region value normalisation. The API region field may include HTML entities
// (e.g. "Europe &amp; North America"), so we always normalise on both sides.
export const REGION_DISPLAY_TO_API = {
  "Africa": "Africa",
  "Arab States": "Arab States",
  "Asia-Pacific": "Asia & the Pacific",
  "Europe": "Europe & North America",
  "Latin America & the Caribbean": "Latin America & the Caribbean",
  "North America": "Europe & North America",
};

// Decode &amp; → & (iteratively for double-encoding) and lowercase for tolerant comparison.
export function normaliseRegion(s) {
  let r = (s || "").trim();
  // Iteratively decode &amp; to handle single or double encoding.
  while (r.includes("&amp;")) {
    r = r.replace(/&amp;/g, "&");
  }
  return r.toLowerCase();
}

// Predefined center + zoom for each region for reliable map zooming.
export const REGION_VIEW = {
  "Africa": { center: [2, 20], zoom: 1 },
  "Arab States": { center: [25, 42], zoom: 2 },
  "Asia-Pacific": { center: [15, 105], zoom: 1 },
  "Europe": { center: [52, 15], zoom: 2 },
  "Latin America & the Caribbean": { center: [-5, -70], zoom: 1 },
  "North America": { center: [50, -100], zoom: 1 },
};

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
