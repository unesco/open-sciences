/**
 * Dashboard API
 * Common HTTP helpers + resource-specific fetch functions.
 */

// ─── API endpoint paths ─────────────────────────────────────────────────────

export const API_PATHS = {
  SURVEY_SECTIONS: "/api/survey-sections",
  SURVEY_QUESTIONS: "/api/survey-questions",
  SURVEY_RESPONSES: "/api/search/survey-responses",
  COUNTRIES: "/api/countries",
  WORDCLOUD: "/api/wordcloud",
  TERM_CONTEXT: "/api/term-context",
};

const isDev =
  (window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1") &&
  window.location.port !== "" &&
  window.location.port !== "80" &&
  window.location.port !== "443";
  
const CMS_BASE = isDev ? "http://localhost:8080/cms" : "/cms";

/**
 * Resolve a CMS-relative asset path (e.g. "/cms/sites/default/files/foo.pdf")
 * to an absolute URL that works both in production and the dev server.
 */
export function resolveCmsAsset(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  if (isDev && path.startsWith("/cms/")) {
    return `http://localhost:8080${path}`;
  }
  return path;
}

// ─── Common HTTP helpers ────────────────────────────────────────────────────

/**
 * Perform a GET request against the CMS base URL.
 * @param {string} path  - e.g. "/api/survey-sections"
 * @returns {Promise<any>} Parsed JSON body
 */
export async function get(path) {
  const response = await fetch(`${CMS_BASE}${path}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(
      `GET ${path} failed: ${response.status} ${response.statusText}`,
    );
  }

  return response.json();
}

/**
 * Perform a POST request against the CMS base URL.
 * @param {string} path  - e.g. "/api/some-endpoint"
 * @param {object} body  - Request payload (will be JSON-serialised)
 * @returns {Promise<any>} Parsed JSON body
 */
export async function post(path, body) {
  const response = await fetch(`${CMS_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(
      `POST ${path} failed: ${response.status} ${response.statusText}`,
    );
  }

  return response.json();
}

// ─── Resource fetch functions ───────────────────────────────────────────────

/**
 * Fetch survey sections (comparison topics) from the CMS.
 * Endpoint: GET /cms/api/survey-sections
 * Response shape (per row): { title: string, id: string }
 */
export async function fetchSurveySections() {
  return get(API_PATHS.SURVEY_SECTIONS);
}

/**
 * Fetch all survey questions from the CMS.
 * Endpoint: GET /cms/api/survey-questions
 * Response shape (per row): { number, text, type, short_name, description, long_description, section }
 */
export async function fetchSurveyQuestions() {
  return get(API_PATHS.SURVEY_QUESTIONS);
}

/**
 * Fetch all survey responses (no filter, no pagination limit).
 * Endpoint: GET /cms/api/search/survey-responses
 */
export async function fetchSurveyResponses() {
  return get(API_PATHS.SURVEY_RESPONSES);
}

/**
 * Fetch survey responses for a single question number.
 * Endpoint: GET /cms/api/search/survey-responses?question_number=<num>
 * @param {string} questionNumber  e.g. "1.1"
 */
export async function fetchSurveyResponsesByQuestion(questionNumber) {
  return get(
    `${API_PATHS.SURVEY_RESPONSES}?question_number=${encodeURIComponent(questionNumber)}`,
  );
}

/**
 * Fetch country → region mapping from the CMS.
 * Endpoint: GET /cms/api/countries
 * Note: region values may contain HTML entities (e.g. "Europe &amp; North America").
 */
export async function fetchCountries() {
  return get(API_PATHS.COUNTRIES);
}

/**
 * Fetch a single country's detail by ISO-3 code.
 * Endpoint: GET /cms/api/countries/<iso3>
 * @param {string} iso3  e.g. "IND", "NLD"
 * @returns {Promise<Array>} Array with a single country object
 */
export async function fetchCountryByIso3(iso3) {
  return get(`${API_PATHS.COUNTRIES}/${encodeURIComponent(iso3)}`);
}

/**
 * Multi-filter survey responses search.
 * Endpoint: GET /cms/api/search/survey-responses-multi-filter
 *
 * @param {Array<{question: string, answers: string[]}>} filters
 *   e.g. [{ question: "1.1", answers: ["Y"] }, { question: "1.3", answers: ["Y", "P"] }]
 * @returns {Promise<{ countries: Array, filters_applied: Array, total_countries: number }>}
 */
export async function fetchMultiFilter(filters) {
  const params = new URLSearchParams();
  filters.forEach((f, i) => {
    params.append(`filters[${i}][question]`, f.question);
    params.append(`filters[${i}][answer]`, f.answers.join(","));
  });
  return get(`/api/search/survey-responses-multi-filter?${params.toString()}`);
}

/**
 * Fetch word cloud terms, optionally filtered by region.
 * Endpoint: GET /cms/api/wordcloud
 * @param {object} [filters]          Optional filters
 * @param {string} [filters.region]   API region value, e.g. "Asia & the Pacific"
 */
export async function fetchWordcloud(filters = {}) {
  const params = new URLSearchParams();
  if (filters.region) params.set("region", filters.region);
  const qs = params.toString();
  return get(`${API_PATHS.WORDCLOUD}${qs ? `?${qs}` : ""}`);
}

/**
 * Fetch term context snippets for a given challenge term.
 * Endpoint: GET /cms/api/term-context
 * @param {string} term               The challenge term, e.g. "lack of funding"
 * @param {object} [filters]          Optional filters
 * @param {string} [filters.region]   API region value
 */
export async function fetchTermContext(term, filters = {}) {
  const params = new URLSearchParams({ term });
  if (filters.region) params.set("region", filters.region);
  return get(`${API_PATHS.TERM_CONTEXT}?${params.toString()}`);
}
