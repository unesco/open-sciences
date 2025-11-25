// Advanced Search Builder
// This file provides a user-friendly interface to build Elasticsearch queries

// ============================================================================
// FILTER CONFIGURATION - Add new filters here
// ============================================================================
const FILTER_CONFIG = [
  {
    id: "author",
    type: "async-search",
    filterType: "query", // Uses q= parameter
    label: "Author Name",
    icon: "user",
    placeholder: "Search and select an author...",
    helpText: "Search and select an author from the database",
    apiUrl:
      "/api/records?q=metadata.creators.person_or_org.name:*{query}*&size=100",
    queryField: "metadata.creators.person_or_org.name",
    responseParser: function (response, searchTerm) {
      const results = [];
      const seen = new Set();

      if (response.hits && response.hits.hits) {
        response.hits.hits.forEach((hit) => {
          if (hit.metadata && hit.metadata.creators) {
            hit.metadata.creators.forEach((creator) => {
              if (creator.person_or_org && creator.person_or_org.name) {
                const name = creator.person_or_org.name;
                if (
                  name.toLowerCase().includes(searchTerm) &&
                  !seen.has(name)
                ) {
                  seen.add(name);
                  results.push({ name: name, value: name, text: name });
                }
              }
            });
          }
        });
      }

      results.sort((a, b) => a.name.localeCompare(b.name));
      return results.slice(0, 10);
    },
  },
  {
    id: "subject",
    type: "async-search",
    filterType: "query", // Uses q= parameter
    label: "Subject / Keyword",
    icon: "tags",
    placeholder: "Search and select a subject...",
    helpText: "Search and select a subject/keyword from the database",
    apiUrl: "/api/records?q=metadata.subjects.subject:*{query}*&size=100",
    queryField: "metadata.subjects.subject",
    responseParser: function (response, searchTerm) {
      const results = [];
      const seen = new Set();

      if (response.hits && response.hits.hits) {
        response.hits.hits.forEach((hit) => {
          if (hit.metadata && hit.metadata.subjects) {
            hit.metadata.subjects.forEach((subjectObj) => {
              if (subjectObj.subject) {
                const subject = subjectObj.subject;
                if (
                  subject.toLowerCase().includes(searchTerm) &&
                  !seen.has(subject)
                ) {
                  seen.add(subject);
                  results.push({
                    name: subject,
                    value: subject,
                    text: subject,
                  });
                }
              }
            });
          }
        });
      }

      results.sort((a, b) => a.name.localeCompare(b.name));
      return results.slice(0, 10);
    },
  },
  {
    id: "affiliation",
    type: "async-search",
    filterType: "query", // Uses q= parameter
    label: "Affiliation",
    icon: "building",
    placeholder: "Search and select an affiliation...",
    helpText: "Search and select an affiliation from the database",
    apiUrl:
      "/api/records?q=metadata.creators.affiliations.name:*{query}*&size=100",
    queryField: "metadata.creators.affiliations.name",
    responseParser: function (response, searchTerm) {
      const results = [];
      const seen = new Set();

      if (response.hits && response.hits.hits) {
        response.hits.hits.forEach((hit) => {
          if (hit.metadata && hit.metadata.creators) {
            hit.metadata.creators.forEach((creator) => {
              if (creator.affiliations) {
                creator.affiliations.forEach((affiliation) => {
                  if (affiliation.name) {
                    const name = affiliation.name;
                    if (
                      name.toLowerCase().includes(searchTerm) &&
                      !seen.has(name)
                    ) {
                      seen.add(name);
                      results.push({ name: name, value: name, text: name });
                    }
                  }
                });
              }
            });
          }
        });
      }

      results.sort((a, b) => a.name.localeCompare(b.name));
      return results.slice(0, 10);
    },
  },
  {
    id: "country",
    type: "async-search",
    filterType: "facet", // Uses f= parameter
    facetName: "publication_country", // The facet name used in URL
    label: "Country",
    icon: "globe",
    placeholder: "Search and select a country...",
    helpText: "Search and select a country from the database",
    apiUrl: "/api/records?f=publication_country:*{query}*&size=100",
    responseParser: function (response, searchTerm) {
      const results = [];
      const seen = new Set();

      if (response.hits && response.hits.hits) {
        response.hits.hits.forEach((hit) => {
          if (hit.custom_fields && hit.custom_fields["publication:country"]) {
            const country = hit.custom_fields["publication:country"];
            if (
              country.toLowerCase().includes(searchTerm) &&
              !seen.has(country)
            ) {
              seen.add(country);
              results.push({ name: country, value: country, text: country });
            }
          }
        });
      }

      results.sort((a, b) => a.name.localeCompare(b.name));
      return results.slice(0, 10);
    },
  },
  {
    id: "funding_org",
    type: "async-search",
    filterType: "facet", // Uses f= parameter
    facetName: "funding_org", // The facet name used in URL
    label: "Funding Organization",
    icon: "money bill alternate",
    placeholder: "Search and select a funding organization...",
    helpText: "Search and select a funding organization from the database",
    apiUrl: "/api/records?f=funding_org:*{query}*&size=100",
    responseParser: function (response, searchTerm) {
      const results = [];
      const seen = new Set();

      if (response.hits && response.hits.hits) {
        response.hits.hits.forEach((hit) => {
          if (
            hit.custom_fields &&
            hit.custom_fields["publication:funding_org"]
          ) {
            const funding_orgs = hit.custom_fields["publication:funding_org"];
            // funding_org is an array, so iterate through it
            if (Array.isArray(funding_orgs)) {
              funding_orgs.forEach((org) => {
                if (org.toLowerCase().includes(searchTerm) && !seen.has(org)) {
                  seen.add(org);
                  results.push({ name: org, value: org, text: org });
                }
              });
            }
          }
        });
      }

      results.sort((a, b) => a.name.localeCompare(b.name));
      return results.slice(0, 10);
    },
  },
];

window.addEventListener("load", function () {
  console.log("Window fully loaded, initializing Advanced Search Builder");

  // Initialize Semantic UI Modal
  const modal = $("#query-builder-modal");
  const clearBtn = document.getElementById("clear-filters-btn");
  const applyBtn = document.getElementById("apply-search-btn");

  // Store dropdown references and search terms
  const dropdowns = {};
  const searchTerms = {};

  // Initialize dropdowns based on configuration
  FILTER_CONFIG.forEach((config) => {
    if (config.type === "async-search") {
      initializeAsyncSearchDropdown(config);
    }
    // Future: Add support for other types (date-range, checkbox, etc.)
  });

  // Initialize async search dropdown
  function initializeAsyncSearchDropdown(config) {
    const dropdown = $(`#${config.id}-dropdown`);
    dropdowns[config.id] = dropdown;
    searchTerms[config.id] = "";

    dropdown.dropdown({
      minCharacters: 2,
      fullTextSearch: true,
      apiSettings: {
        url: config.apiUrl,
        cache: false,
        throttle: 300,
        beforeXHR: function (xhr, settings) {
          const url = settings.url || xhr.url;
          const urlParams = new URLSearchParams(url.split("?")[1]);
          const searchQuery = urlParams.get("q");
          const queryMatch = searchQuery
            ? searchQuery.match(/\*([^*]+)\*/)
            : null;
          searchTerms[config.id] = queryMatch
            ? queryMatch[1].toLowerCase()
            : "";
          return xhr;
        },
        onResponse: function (response) {
          const results = config.responseParser(
            response,
            searchTerms[config.id]
          );
          return { success: true, results: results };
        },
      },
      allowAdditions: true,
      forceSelection: false,
      onChange: function () {
        updateBadge();
      },
    });
  }

  // Parse URL parameters and initialize form
  function initializeFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const existingQuery = urlParams.get("q") || "";
    const facetFilters = urlParams.getAll("f");

    console.log("Parsing URL - query:", existingQuery, "facets:", facetFilters);

    // Parse query string filters (metadata fields)
    if (existingQuery) {
      FILTER_CONFIG.forEach((config) => {
        if (config.filterType === "query") {
          const escapedField = config.queryField.replace(/\./g, "\\.");
          const regex = new RegExp(`${escapedField}:"([^"]+)"`);
          const match = existingQuery.match(regex);

          if (match && dropdowns[config.id]) {
            const value = match[1];
            console.log(`Setting ${config.id} from query:`, value);
            dropdowns[config.id].dropdown("set exactly", value);
          }
        }
      });
    }

    // Parse facet filters
    facetFilters.forEach((facet) => {
      const colonIndex = facet.indexOf(":");
      if (colonIndex === -1) return;

      const facetName = facet.substring(0, colonIndex);
      const facetValue = facet.substring(colonIndex + 1);

      // Find the config with matching facetName
      FILTER_CONFIG.forEach((config) => {
        if (config.filterType === "facet" && config.facetName === facetName) {
          if (dropdowns[config.id]) {
            console.log(`Setting ${config.id} from facet:`, facetValue);
            dropdowns[config.id].dropdown("set exactly", facetValue);
          }
        }
      });
    });

    updateBadge();
  }

  // Update badge with filter count
  function updateBadge() {
    const badge = document.getElementById("filter-badge");
    if (!badge) return;

    let totalFilters = 0;

    FILTER_CONFIG.forEach((config) => {
      if (dropdowns[config.id]) {
        const value = dropdowns[config.id].dropdown("get value");
        if (value && value.trim()) {
          totalFilters++;
        }
      }
    });

    console.log("Badge update - Total filters:", totalFilters);

    if (totalFilters > 0) {
      badge.textContent = totalFilters;
      badge.style.display = "flex";
    } else {
      badge.style.display = "none";
    }
  }

  // Build query parameters from dropdown values
  function buildQueryParams() {
    const params = new URLSearchParams();
    const queryParts = [];

    FILTER_CONFIG.forEach((config) => {
      if (dropdowns[config.id]) {
        const value = dropdowns[config.id].dropdown("get value");
        if (value && value.trim()) {
          if (config.filterType === "facet") {
            // Facet-based filters use f= parameter
            params.append("f", `${config.facetName}:${value.trim()}`);
          } else {
            // Query-based filters use q= parameter
            queryParts.push(`${config.queryField}:"${value.trim()}"`);
          }
        }
      }
    });

    // Build the query string (for metadata fields)
    if (queryParts.length > 0) {
      params.set("q", queryParts.join(" AND "));
    }

    return params;
  }

  // Clear all filters
  clearBtn.addEventListener("click", function () {
    console.log("Clear button clicked");
    FILTER_CONFIG.forEach((config) => {
      if (dropdowns[config.id]) {
        dropdowns[config.id].dropdown("clear");
      }
    });
    updateBadge();
  });

  // Apply search
  applyBtn.addEventListener("click", function () {
    console.log("Apply search clicked");
    const params = buildQueryParams();
    console.log("Built params:", params.toString());

    modal.modal("hide");

    if (params.toString()) {
      window.location.href = "/search?" + params.toString() + "&page=1";
    } else {
      window.location.href = "/search";
    }
  });

  // Attach click handler to trigger button
  const triggerBtn = document.getElementById("query-builder-trigger");
  if (triggerBtn) {
    triggerBtn.addEventListener("click", function (e) {
      e.preventDefault();
      console.log("Opening query builder modal");
      modal.modal("show");
    });
  }

  // Initialize form from URL parameters
  initializeFromURL();

  console.log("Advanced Search Builder initialized successfully");
});
