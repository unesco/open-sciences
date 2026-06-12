import React, { useState, useEffect } from "react";
import {
  Card,
  Loader,
  Dimmer,
  Checkbox,
  Label,
} from "semantic-ui-react";
import axios from "axios";

// Global cache to persist across component remounts
let cachedData = null;
let fetchPromise = null;

const ResourceTypeFacet = () => {
  const [data, setData] = useState(cachedData || []);
  const [loading, setLoading] = useState(!cachedData);
  const [selectedType, setSelectedType] = useState(null); // Single selection

  // Parse URL to get current filter (single selection)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const facetFilters = urlParams.getAll("f");

    // Extract resource_type filter (supports both parent and inner formats)
    const resourceTypeFilter = facetFilters.find((f) =>
      f.includes("resource_type:"),
    );

    if (resourceTypeFilter) {
      // Check if it's an inner (child) type: "resource_type:parent+inner:child"
      const innerMatch = resourceTypeFilter.match(/\+inner:([^&]+)/);
      if (innerMatch) {
        setSelectedType(innerMatch[1]);
      } else {
        // It's a parent type: "resource_type:parent"
        const parentMatch = resourceTypeFilter.match(/resource_type:([^+&]+)/);
        if (parentMatch) {
          setSelectedType(parentMatch[1]);
        }
      }
    }
  }, []);

  // Fetch resource types from InvenioRDM aggregations
  useEffect(() => {
    // Invalidate cache when search context changes
    cachedData = null;

    // If we already have cached data, use it
    if (cachedData) {
      setData(cachedData);
      setLoading(false);
      return;
    }

    // If a fetch is already in progress, wait for it
    if (fetchPromise) {
      fetchPromise.then((result) => {
        setData(result);
        setLoading(false);
      });
      return;
    }

    // Start a new fetch - use custom backend for filtered aggregations
    setLoading(true);

    // Get current search context from URL
    const urlParams = new URLSearchParams(window.location.search);
    const searchQuery = urlParams.get("q") || "";
    const facetFilters = urlParams
      .getAll("f")
      .filter((f) => !f.startsWith("resource_type:"));

    // Build URL for custom backend endpoint
    let url = "/data/search?field=resource_type&size=1000";
    if (searchQuery) {
      url += `&searchQuery=${encodeURIComponent(searchQuery)}`;
    }
    if (facetFilters.length > 0) {
      url += `&facetFilters=${encodeURIComponent(facetFilters.join(","))}`;
    }

    fetchPromise = axios
      .get(url)
      .then((response) => {
        const results = response.data.results || [];
        const hierarchy = organizeHierarchyFromBackend(results);
        cachedData = hierarchy;
        return hierarchy;
      })
      .catch((error) => {
        console.error("Error fetching resource types:", error);
        return [];
      })
      .finally(() => {
        fetchPromise = null;
      });

    fetchPromise.then((result) => {
      setData(result);
      setLoading(false);
    });
  }, [window.location.search]); // Re-fetch when search context changes

  // Helper function to format resource type labels
  const formatLabel = (typeId) => {
    // For child types like "publication-article", extract and format the subtype
    if (typeId.includes("-")) {
      // Remove the parent prefix (e.g., "publication-article" -> "article")
      const parts = typeId.split("-");
      const subtype = parts.slice(1).join("-"); // Get everything after first hyphen
      // Convert hyphenated words to proper case: "journal-article" -> "Journal Article"
      return subtype
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
    }
    // For parent types, just capitalize
    return typeId.charAt(0).toUpperCase() + typeId.slice(1);
  };

  // Flatten the backend results into a single list of leaf resource types.
  // Each item carries its parentValue (e.g. "publication") solely for building
  // the URL filter — there is no parent row or expand/collapse in the UI.
  const organizeHierarchyFromBackend = (results) => {
    const flatItems = [];

    results.forEach((item) => {
      const typeId = item.value || item.name;

      if (typeId.includes("-")) {
        // e.g. "publication-article" → rendered directly as "Article"
        flatItems.push({
          value: typeId,
          label: formatLabel(typeId), // strips "publication-" prefix, capitalises
          parentValue: typeId.split("-")[0], // "publication" — used only for URL filter
          count: item.count || 0,
        });
      } else {
        // safety fallback for any remaining standalone type
        flatItems.push({
          value: typeId,
          label: formatLabel(typeId),
          parentValue: null,
          count: item.count || 0,
        });
      }
    });

    return flatItems; // no nesting
  };

  const handleItemClick = (typeValue, parentValue = null) => {
    const urlParams = new URLSearchParams(window.location.search);

    // Remove existing resource_type filters
    const facetFilters = urlParams
      .getAll("f")
      .filter((f) => !f.includes("resource_type:"));
    urlParams.delete("f");
    facetFilters.forEach((f) => urlParams.append("f", f));

    // Toggle selection: if clicking the same item, deselect it
    const newSelectedType = selectedType === typeValue ? null : typeValue;

    // Add new filter if selected
    if (newSelectedType) {
      let filterValue;
      if (parentValue) {
        // Child type: use format "resource_type:parent+inner:child"
        filterValue = `resource_type:${parentValue}+inner:${newSelectedType}`;
      } else {
        // Parent type: use format "resource_type:parent"
        filterValue = `resource_type:${newSelectedType}`;
      }
      urlParams.append("f", filterValue);
    }

    // Reset to page 1
    urlParams.set("page", "1");

    // Navigate to new URL
    window.location.href = `${
      window.location.pathname
    }?${urlParams.toString()}`;
  };

  return (
    <Card
      className="borderless facet"
      style={{ boxShadow: "none", border: "none" }}
    >
      <Card.Content style={{ padding: "0.65rem" }}>
        <Card.Header
          as="h2"
          style={{
            color: "#212121",
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-start",
            marginBottom: "0.75rem",
            fontSize: "0.92rem",
            fontWeight: 600,
          }}
        >
          Resources Type
        </Card.Header>
        <div
          style={{
            maxHeight: "300px",
            overflowY: "auto",
            position: "relative",
          }}
        >
          {loading ? (
            <div style={{ position: "relative" }}>
              <Dimmer active inverted>
                <Loader size="small" />
              </Dimmer>
              <div style={{ opacity: 0.3, pointerEvents: "none" }}>
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "0.6rem 0.8rem",
                      marginBottom: "0.5rem",
                    }}
                  >
                    <div
                      style={{ display: "flex", alignItems: "center", flex: 1 }}
                    >
                      <Checkbox
                        radio
                        disabled
                        label="Loading..."
                        style={{ fontSize: "0.92rem" }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : data.length === 0 ? (
            <div
              style={{
                padding: "1rem",
                textAlign: "center",
                color: "#767676",
              }}
            >
              No resource types found
            </div>
          ) : (
            data.map((item) => (
              <div
                key={item.value}
                role="button"
                tabIndex={0}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.6rem 0.8rem",
                  cursor: "pointer",
                }}
                onClick={() => handleItemClick(item.value, item.parentValue)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    handleItemClick(item.value, item.parentValue);
                  }
                }}
              >
                <Checkbox
                  radio
                  label={
                    <label
                      style={{
                        cursor: "pointer",
                        fontSize: "0.92rem",
                        color: "rgba(0, 0, 0, 0.87)",
                      }}
                    >
                      {item.label}
                    </label>
                  }
                  checked={selectedType === item.value}
                />
                <Label
                  size="mini"
                  circular
                  style={{
                    backgroundColor: "#e0e1e2",
                    color: "rgba(0, 0, 0, 0.6)",
                    minWidth: "2rem",
                    textAlign: "center",
                  }}
                >
                  {item.count}
                </Label>
              </div>
            ))
          )}
        </div>
      </Card.Content>
    </Card>
  );
};

export default ResourceTypeFacet;
