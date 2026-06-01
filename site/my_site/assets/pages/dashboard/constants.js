
/** Blue-shade cycle for answer/region segments (index → colour). */
export const TABS = [
  { id: "global", label: "Global overview" },
  { id: "comparison", label: "Comparison across countries & regions" },
  { id: "challenges", label: "Open Science challenges" },
];

export const DISCLAIMER_TEXT =
  "The Dashboards present information as reported by the Member States. " +
  "UNESCO does not independently verify the accuracy or completeness of the " +
  "submitted information. An AI model, Claude Opus 4.5, was used to assist " +
  "in preparing initial draft summaries for the Country Profiles. These " +
  "drafts were subsequently thoroughly reviewed, revised and approved by " +
  "the UNESCO team. Personal data contained in the original national " +
  "submission files, including respondents\u2019 contact details, was removed " +
  "before the files were published as supporting materials accompanying the " +
  "Dashboards.";

/** Blue-shade cycle for answer/region segments (index → colour). */
export const BLUE_PALETTE = [
  "#0d3b6e", // deep navy
  "#1a5c9e", // dark blue
  "#3a9bd5", // medium blue
  "#6db8e8", // light blue
  "#a3d4f5", // pale blue
  "#c8e6f9", // very pale blue
];

// Fixed colours for the standard closed-answer options, shared by every
// comparison chart (donuts, region/country breakdowns, mini donuts, legends).
export const COLOR_YES               = "#0077D4";
export const COLOR_NO                = "#7F888F";
export const COLOR_PARTLY            = "#4D9ACC";
export const COLOR_UNDER_DEVELOPMENT = "#0E4280";
export const COLOR_NA_ANSWER         = "#D5DADD";

// ── N/A handling ──────────────────────────────────────────────────────────────
// Canonical N/A label shown in charts/legends.
export const NA_LABEL = "N/A";
// Note appended to info tooltips/modals when an N/A answer exists.
export const NA_INFO_NOTE =
  'N/A in this case means "Not applicable, no answer or no clear answer"';
// Lower-cased variants that should all be treated as N/A.
export const NA_LABEL_VARIANTS = [
  "",
  "n/a",
  "na",
  "no answer",
  "non applicable",
  "not applicable",
];

// ── Chart.js CDN ──────────────────────────────────────────────────────────────
export const CHARTJS_CDN_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js";
export const CHARTJS_CDN_ID  = "chartjs-cdn";

// ── Choropleth / map colours ──────────────────────────────────────────────────
export const COLOR_NO_DATA      = "#D5DADD";
export const COLOR_BORDER       = "#ffffff";
export const COLOR_PARTICIPATED = "#4C5054";
export const COLOR_MATCHES      = "#B2D6F2";

// ── World GeoJSON ─────────────────────────────────────────────────────────────
export const WORLD_GEOJSON_URL =
  "https://cdn.jsdelivr.net/gh/johan/world.geo.json@master/countries.geo.json";

// ── Regions ───────────────────────────────────────────────────────────────────
export const ALL_REGIONS = "All regions";

export const REGIONS = [
  { label: "All regions",                    apiValue: null,                             view: null },
  { label: "Africa",                         apiValue: "Africa",                         view: { center: [5,    20],  zoom: 2.5 } },
  { label: "Arab States",                    apiValue: "Arab States",                    view: { center: [25,   42],  zoom: 3.5 } },
  { label: "Asia-Pacific",                   apiValue: "Asia & the Pacific",             view: { center: [25,   100], zoom: 2.5 } },
  { label: "Europe & North America",         apiValue: "Europe & North America",         view: { center: [50,   -20], zoom: 3 } },
  { label: "Latin America & the Caribbean",  apiValue: "Latin America & the Caribbean",  view: { center: [-15,  -60], zoom: 2.5 } },
];

// Fixed colour per region — keyed by lower-cased apiValue, resolved via getRegionColor in utils.
export const REGION_COLORS = {
  "africa":                        "#0d3b6e",
  "asia & the pacific":            "#1a5c9e",
  "europe & north america":        "#3a9bd5",
  "arab states":                   "#6db8e8",
  "latin america & the caribbean": "#a3d4f5",
};

// Derived lookups
export const REGION_LABELS = REGIONS.map((r) => r.label);

export const REGION_DISPLAY_TO_API = Object.fromEntries(
  REGIONS.filter((r) => r.apiValue).map((r) => [r.label, r.apiValue])
);

export const REGION_VIEW = Object.fromEntries(
  REGIONS.filter((r) => r.view).map((r) => [r.label, r.view])
);

// ── Country detail sections ───────────────────────────────────────────────────
export const COUNTRY_SECTIONS = [
  {
    id: "promote_culture",
    label:
      "Promoting a common understanding of open science, associated benefits, and challenges, as well as diverse paths to open science",
    field: "field_info_promote_culture",
  },
  {
    id: "policy",
    label: "Developing an enabling policy environment for open science",
    field: "field_info_policy",
  },
  {
    id: "funding_infra",
    label: "Investing in open science infrastructures",
    field: "field_info_funding_infra",
  },
  {
    id: "funding_training",
    label:
      "Investing in human resources, training, education, digital literacy, and capacity building for open science",
    field: "field_info_funding_training",
  },
  {
    id: "promoting",
    label: "Fostering a culture of open science and aligning incentives for open science",
    field: "field_info_promoting",
  },
  {
    id: "promote_cooperation",
    label: "Promoting innovative approaches for open science at different stages of the scientific process",
    field: "field_info_promote_cooperation",
  },
  {
    id: "promote_inovation",
    label:
      "Promoting international and multi-stakeholder cooperation in the context of open science and with a view to reducing digital, technological, and knowledge gaps",
    field: "field_info_promote_inovation",
  },
];
