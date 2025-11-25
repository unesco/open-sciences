// Advanced Search Builder
// This file provides a user-friendly interface to build Elasticsearch queries

window.addEventListener("load", function () {
  console.log("Window fully loaded, initializing Advanced Search Builder");

  // Initialize Semantic UI Modal
  const modal = $("#query-builder-modal");
  const clearBtn = document.getElementById("clear-filters-btn");
  const applyBtn = document.getElementById("apply-search-btn");

  // Initialize elements
  const authorDropdown = $("#author-dropdown");
  let currentSearchTerm = "";

  // Configure author dropdown with API search (single selection)
  authorDropdown.dropdown({
    minCharacters: 2,
    fullTextSearch: true,
    apiSettings: {
      url: "/api/records?q=metadata.creators.person_or_org.name:*{query}*&size=100",
      cache: false,
      throttle: 300,
      beforeXHR: function (xhr, settings) {
        const url = settings.url || xhr.url;
        const urlParams = new URLSearchParams(url.split("?")[1]);
        const searchQuery = urlParams.get("q");
        const queryMatch = searchQuery
          ? searchQuery.match(/\*([^*]+)\*/)
          : null;
        currentSearchTerm = queryMatch ? queryMatch[1].toLowerCase() : "";
        return xhr;
      },
      onResponse: function (response) {
        const results = [];
        const seenAuthors = new Set();

        if (response.hits && response.hits.hits) {
          response.hits.hits.forEach((hit) => {
            if (hit.metadata && hit.metadata.creators) {
              hit.metadata.creators.forEach((creator) => {
                if (creator.person_or_org && creator.person_or_org.name) {
                  const name = creator.person_or_org.name;
                  if (
                    name.toLowerCase().includes(currentSearchTerm) &&
                    !seenAuthors.has(name)
                  ) {
                    seenAuthors.add(name);
                    results.push({ name: name, value: name, text: name });
                  }
                }
              });
            }
          });
        }

        results.sort((a, b) => a.name.localeCompare(b.name));
        return { success: true, results: results.slice(0, 10) };
      },
    },
    allowAdditions: true,
    forceSelection: false,
    onChange: function () {
      updateBadge();
    },
  });

  // Parse URL parameters and initialize form
  function initializeFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const existingQuery = urlParams.get("q") || "";
    console.log("Parsing URL query:", existingQuery);

    if (!existingQuery) {
      updateBadge();
      return;
    }

    // Parse author from URL (exact match with quotes)
    const authorMatch = existingQuery.match(
      /metadata\.creators\.person_or_org\.name:"([^"]+)"/
    );
    if (authorMatch) {
      const authorName = authorMatch[1];
      console.log("Setting author from URL:", authorName);
      authorDropdown.dropdown("set exactly", authorName);
    }

    updateBadge();
  }

  // Update badge with filter count
  function updateBadge() {
    const badge = document.getElementById("filter-badge");
    if (!badge) return;

    const authorValue = authorDropdown.dropdown("get value");
    const hasAuthor = authorValue && authorValue.trim() ? 1 : 0;

    console.log("Badge update - Has author:", hasAuthor);

    if (hasAuthor > 0) {
      badge.textContent = hasAuthor;
      badge.style.display = "flex";
    } else {
      badge.style.display = "none";
    }
  }

  // Build Elasticsearch query from dropdown value
  function buildQuery() {
    const authorValue = authorDropdown.dropdown("get value");

    if (authorValue && authorValue.trim()) {
      return `metadata.creators.person_or_org.name:"${authorValue.trim()}"`;
    }

    return "";
  }

  // Clear all filters
  clearBtn.addEventListener("click", function () {
    console.log("Clear button clicked");
    authorDropdown.dropdown("clear");
    updateBadge();
  });

  // Apply search
  applyBtn.addEventListener("click", function () {
    console.log("Apply search clicked");
    const query = buildQuery();
    console.log("Built query:", query);

    modal.modal("hide");

    if (query) {
      window.location.href =
        "/search?q=" + encodeURIComponent(query) + "&page=1";
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
