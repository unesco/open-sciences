/**
 * Inject Advanced Search button as first facet card in the facets list
 */

(function () {
  console.log("Advanced search link injection script loaded");

  function injectAdvancedSearchLink() {
    // Check if already injected
    if (document.getElementById("advanced-search-facet-card")) {
      console.log("Advanced search already injected");
      return;
    }

    // Try multiple strategies to find facets
    let firstFacet = null;
    let facetsContainer = null;

    // Strategy 1: Look for visible facet cards
    const allFacets = document.querySelectorAll(".ui.card.borderless.facet");
    console.log(`Found ${allFacets.length} total facet cards`);

    for (const facet of allFacets) {
      const rect = facet.getBoundingClientRect();
      const isVisible = rect.width > 0 && rect.height > 0;
      console.log(
        `Facet visibility - width: ${rect.width}, height: ${rect.height}, visible: ${isVisible}`
      );

      if (isVisible) {
        firstFacet = facet;
        facetsContainer = facet.parentElement;
        console.log("✓ Found visible facet in:", facetsContainer.className);
        break;
      }
    }

    // Strategy 2: If no visible facet found, use the first one anyway
    if (!firstFacet && allFacets.length > 0) {
      firstFacet = allFacets[0];
      facetsContainer = firstFacet.parentElement;
      console.log(
        "Using first facet (may not be visible):",
        facetsContainer.className
      );
    }

    if (!firstFacet) {
      console.warn("No facet cards found at all, retrying...");
      setTimeout(injectAdvancedSearchLink, 500);
      return;
    }

    console.log("✓ Injecting advanced search before facet");

    // Ensure parent is visible
    if (facetsContainer) {
      facetsContainer.style.display = "";
      facetsContainer.style.visibility = "";
    }

    // Create the advanced search card matching facet style exactly
    const advancedSearchCard = document.createElement("div");
    advancedSearchCard.id = "advanced-search-facet-card";
    advancedSearchCard.className = "ui card borderless facet";

    // Match exact padding and styling of other facet cards
    advancedSearchCard.innerHTML = `
      <div class="content">
        <a href="#" id="facets-query-builder-link" style="
          background: transparent;
          color: #0073b7;
          padding: 0;
          margin: 0;
          text-decoration: none;
          display: flex;
          align-items: center;
          gap: 6px;
          font-weight: 500;
          transition: color 0.2s ease;
          border: none;
          cursor: pointer;
          font-size: 1em;
          line-height: 1.4em;
        ">
          <i class="sliders horizontal icon" style="
            margin: 0 !important; 
            color: #0073b7;
            font-size: 1em;
            line-height: 1;
            display: inline-flex;
            align-items: center;
          "></i>
          <span style="flex: 1; line-height: 1.4em;">Advanced Search</span>
          <span id="facets-advanced-search-badge" class="ui circular mini label" style="
            background: #ff4444;
            color: white;
            display: none;
            font-size: 0.7em;
            padding: 4px 7px;
            margin-left: 4px;
          ">0</span>
        </a>
      </div>
    `;

    // Insert before the first facet
    facetsContainer.insertBefore(advancedSearchCard, firstFacet);

    // Add click handler to open modal
    const link = document.getElementById("facets-query-builder-link");
    link.addEventListener("click", function (e) {
      e.preventDefault();
      console.log("Opening advanced search modal from facets");
      const modal = window.jQuery("#query-builder-modal");
      if (modal && modal.modal) {
        modal.modal("show");
      } else {
        console.error("Modal not available");
      }
    });

    // Ant Design link button hover effect
    link.addEventListener("mouseenter", function () {
      this.style.color = "#005a8c";
      this.querySelector("i").style.color = "#005a8c";
    });

    link.addEventListener("mouseleave", function () {
      this.style.color = "#0073b7";
      this.querySelector("i").style.color = "#0073b7";
    });

    console.log("✓ Advanced search card injected successfully");
  }

  // Watch for facets to be rendered by React
  function waitForFacets() {
    const observer = new MutationObserver(function (mutations, obs) {
      const facets = document.querySelectorAll(".ui.card.borderless.facet");
      if (facets.length > 0) {
        console.log("Facets detected, injecting advanced search");
        obs.disconnect();
        injectAdvancedSearchLink();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    // Fallback: try after 500ms if observer doesn't catch it
    setTimeout(function () {
      if (!document.getElementById("advanced-search-facet-card")) {
        injectAdvancedSearchLink();
      }
    }, 500);
  }

  // Start watching after DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", waitForFacets);
  } else {
    waitForFacets();
  }
})();
