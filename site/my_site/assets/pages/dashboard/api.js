/**
 * Dashboard API
 * Common HTTP helpers + resource-specific fetch functions.
 */

// In development (localhost) the CMS is accessed directly on port 8081.
// In production it is proxied by nginx under /cms (same origin, no CORS).
const isDev =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1";
const CMS_BASE = isDev ? "http://localhost:8080/cms" : "/cms";

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
    throw new Error(`GET ${path} failed: ${response.status} ${response.statusText}`);
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
    throw new Error(`POST ${path} failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// ─── Resource fetch functions ───────────────────────────────────────────────

/**
 * Fetch survey sections (comparison topics) from the CMS.
 * Source: views.view.survey_sections – REST export display
 * Endpoint: GET /cms/api/survey-sections
 * Response shape (per row): { title: string, id: string }
 */
export async function fetchSurveySections() {
  return get("/api/survey-sections");
}

/**
 * Fetch all survey questions from the CMS.
 * Endpoint: GET /cms/api/survey-questions
 * Response shape (per row): { number, text, type, short_name, description, long_description, section }
 */
export async function fetchSurveyQuestions() {
  return get("/api/survey-questions");
}

/**
 * Fetch all survey responses (no filter, no pagination limit).
 * Endpoint: GET /cms/api/search/survey-responses
 */
export async function fetchSurveyResponses() {
  return get("/api/search/survey-responses");
}


/**
 * Fetch survey responses for a single question number.
 * Endpoint: GET /cms/api/search/survey-responses?question_number=<num>
 * @param {string} questionNumber  e.g. "1.1"
 */
export async function fetchSurveyResponsesByQuestion(questionNumber) {
  return get(`/api/search/survey-responses?question_number=${encodeURIComponent(questionNumber)}`);
}

/**
 * Fetch country → region mapping from the CMS.
 * Endpoint: GET /cms/api/countries
 * Response shape (per item): { name, group, iso_3, region }
 * Note: region values may contain HTML entities (e.g. "Europe &amp; North America").
 */
export async function fetchCountries() {
  return get("/api/countries");
}
