
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

export const COLOR_YES = "#0077D4";
export const COLOR_NO  = "#E7E6E6";

// ── Chart.js CDN ──────────────────────────────────────────────────────────────
export const CHARTJS_CDN_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js";
export const CHARTJS_CDN_ID  = "chartjs-cdn";

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
