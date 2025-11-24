// Advanced Search Builder
// This file provides a user-friendly interface to build Elasticsearch queries

window.addEventListener("load", function () {
  console.log("Window fully loaded, initializing Advanced Search Builder");

  let authorFilters = [];
  let subjectFilters = [];

  // Parse existing query from URL
  const urlParams = new URLSearchParams(window.location.search);
  const existingQuery = urlParams.get("q") || "";
  console.log("Existing query:", existingQuery);

  // Initialize Semantic UI Modal
  const modal = $("#query-builder-modal");

  // Attach click handler to the trigger button
  const triggerBtn = document.getElementById("query-builder-trigger");
  if (triggerBtn) {
    triggerBtn.addEventListener("click", function (e) {
      e.preventDefault();
      console.log("Opening query builder modal");
      modal.modal("show");
    });
    console.log("Query builder trigger button ready");
  } else {
    console.error("Query builder trigger button not found");
  }

  const addAuthorBtn = document.getElementById("add-author-btn");
  const addSubjectBtn = document.getElementById("add-subject-btn");
  const clearBtn = document.getElementById("clear-filters-btn");
  const applyBtn = document.getElementById("apply-search-btn");
  const authorInput = document.getElementById("author-input");
  const subjectInput = document.getElementById("subject-input");

  console.log("Elements found:", {
    addAuthorBtn: !!addAuthorBtn,
    addSubjectBtn: !!addSubjectBtn,
    clearBtn: !!clearBtn,
    applyBtn: !!applyBtn,
    authorInput: !!authorInput,
    subjectInput: !!subjectInput,
  });

  if (!addAuthorBtn || !clearBtn || !applyBtn || !authorInput) {
    console.error("Some elements not found!");
    return;
  }

  // Add author filter
  addAuthorBtn.addEventListener("click", function () {
    console.log("Add author button clicked");
    const author = authorInput.value.trim();
    console.log("Author value:", author);

    if (author && !authorFilters.includes(author)) {
      authorFilters.push(author);
      renderFilters();
      updateBadge();
      authorInput.value = "";
    }
  });

  // Allow Enter key to add author
  authorInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      addAuthorBtn.click();
    }
  });

  // Add subject filter
  addSubjectBtn.addEventListener("click", function () {
    console.log("Add subject button clicked");
    const subject = subjectInput.value.trim();
    console.log("Subject value:", subject);

    if (subject && !subjectFilters.includes(subject)) {
      subjectFilters.push(subject);
      renderFilters();
      updateBadge();
      subjectInput.value = "";
    }
  });

  // Allow Enter key to add subject
  subjectInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      addSubjectBtn.click();
    }
  });

  // Clear all filters
  clearBtn.addEventListener("click", function () {
    console.log("Clear button clicked");
    authorFilters = [];
    subjectFilters = [];
    renderFilters();
    updateBadge();
  });

  // Apply search
  applyBtn.addEventListener("click", function () {
    console.log("Apply search clicked");
    console.log("Author filters:", authorFilters);
    console.log("Subject filters:", subjectFilters);
    const query = buildQuery();
    console.log("Built query:", query);

    // Close modal
    modal.modal("hide");

    if (query) {
      const searchUrl = "/search?q=" + encodeURIComponent(query) + "&page=1";
      console.log("Redirecting to:", searchUrl);
      window.location.href = searchUrl;
    } else {
      console.log("No query, redirecting to /search");
      window.location.href = "/search";
    }
  });

  // Update badge with filter count
  function updateBadge() {
    const badge = document.getElementById("filter-badge");
    if (!badge) return;

    const totalFilters = authorFilters.length + subjectFilters.length;
    if (totalFilters > 0) {
      badge.textContent = totalFilters;
      badge.style.display = "flex";
      badge.style.alignItems = "center";
      badge.style.justifyContent = "center";
    } else {
      badge.style.display = "none";
    }
  }

  // Build Elasticsearch query
  function buildQuery() {
    const queries = [];

    if (authorFilters.length > 0) {
      const authorQueries = authorFilters.map(
        (author) => `metadata.creators.person_or_org.name:*${author}*`
      );
      queries.push(authorQueries.join(" AND "));
    }

    if (subjectFilters.length > 0) {
      const subjectQueries = subjectFilters.map(
        (subject) => `metadata.subjects.subject:*${subject}*`
      );
      queries.push(subjectQueries.join(" AND "));
    }

    return queries.join(" AND ");
  }

  // Render active filters
  function renderFilters() {
    const container = document.getElementById("active-filters");

    if (authorFilters.length === 0 && subjectFilters.length === 0) {
      container.innerHTML =
        '<div style="color: #999; font-style: italic;">No filters added yet. Add authors or subjects above.</div>';
      return;
    }

    let filtersHTML =
      '<strong style="color: #0073b7;">Active Filters:</strong><div style="margin-top: 0.5em;">';

    // Author filters
    authorFilters.forEach((author, index) => {
      filtersHTML += `
        <div class="ui label" style="background-color: #0073b7; color: white; margin: 0.25em; box-shadow: none;">
          <i class="user icon"></i> Author: ${author}
          <i class="delete icon" style="cursor: pointer;" data-filter-type="author" data-filter-index="${index}"></i>
        </div>
      `;
    });

    // Subject filters
    subjectFilters.forEach((subject, index) => {
      filtersHTML += `
        <div class="ui label" style="background-color: #28a745; color: white; margin: 0.25em; box-shadow: none;">
          <i class="tags icon"></i> Subject: ${subject}
          <i class="delete icon" style="cursor: pointer;" data-filter-type="subject" data-filter-index="${index}"></i>
        </div>
      `;
    });

    filtersHTML += "</div>";
    container.innerHTML = filtersHTML;

    // Attach event listeners to delete icons
    container.querySelectorAll(".delete.icon").forEach((icon) => {
      icon.addEventListener("click", function () {
        const filterType = this.getAttribute("data-filter-type");
        const index = parseInt(this.getAttribute("data-filter-index"));
        console.log(`Removing ${filterType} filter at index:`, index);

        if (filterType === "author") {
          authorFilters.splice(index, 1);
        } else if (filterType === "subject") {
          subjectFilters.splice(index, 1);
        }

        renderFilters();
        updateBadge();
      });
    });
  }

  // Initialize: parse existing query if present
  if (existingQuery) {
    // Parse author filters
    if (existingQuery.includes("metadata.creators.person_or_org.name:")) {
      const authorMatches = existingQuery.match(
        /metadata\.creators\.person_or_org\.name:\*([^*]+)\*/g
      );
      if (authorMatches) {
        authorFilters = authorMatches.map((m) =>
          m.replace(/metadata\.creators\.person_or_org\.name:\*([^*]+)\*/, "$1")
        );
      }
    }

    // Parse subject filters
    if (existingQuery.includes("metadata.subjects.subject:")) {
      const subjectMatches = existingQuery.match(
        /metadata\.subjects\.subject:\*([^*]+)\*/g
      );
      if (subjectMatches) {
        subjectFilters = subjectMatches.map((m) =>
          m.replace(/metadata\.subjects\.subject:\*([^*]+)\*/, "$1")
        );
      }
    }

    if (authorFilters.length > 0 || subjectFilters.length > 0) {
      // Don't open modal automatically, just render the filters
      renderFilters();
      updateBadge();
    }
  }

  // Initial render
  renderFilters();
  updateBadge();

  console.log("Advanced Search Builder initialized successfully");
});
