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
