import React, { useState, useEffect } from "react";
import {
  Card,
  Icon,
  Popup,
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
  const [expandedParents, setExpandedParents] = useState(
    new Set(["publication"])
  ); // Expand by default

  // Parse URL to get current filter (single selection)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const facetFilters = urlParams.getAll("f");

    // Extract resource_type filter (supports both parent and inner formats)
    const resourceTypeFilter = facetFilters.find((f) =>
      f.includes("resource_type:")
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
    const facetFilters = urlParams.getAll("f").filter(f => !f.startsWith("resource_type:"));
    
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

  // Organize InvenioRDM aggregation buckets into parent-child hierarchy
  const organizeHierarchy = (buckets) => {
    const parents = buckets.map((bucket) => ({
      value: bucket.key,
      label: bucket.label,
      count: bucket.doc_count,
      children: (bucket.inner?.buckets || []).map((child) => ({
        value: child.key,
        label: child.label,
        count: child.doc_count,
      })),
    }));

    return parents;
  };

  // Organize results from custom backend into parent-child hierarchy
  const organizeHierarchyFromBackend = (results) => {
    // Group by parent type (e.g., "publication", "image")
    const parentMap = {};
    
    results.forEach((item) => {
      const typeId = item.value || item.name;
      
      // Split on hyphen to determine parent-child relationship
      if (typeId.includes("-")) {
        const [parent, child] = typeId.split("-", 2);
        if (!parentMap[parent]) {
          parentMap[parent] = {
            value: parent,
            label: parent.charAt(0).toUpperCase() + parent.slice(1),
            count: 0,
            children: [],
          };
        }
        parentMap[parent].children.push({
          value: typeId,
          label: item.text || item.name || typeId,
          count: item.count || 0,
        });
        parentMap[parent].count += item.count || 0;
      } else {
        // Parent type
        if (!parentMap[typeId]) {
          parentMap[typeId] = {
            value: typeId,
            label: item.text || item.name || typeId,
            count: item.count || 0,
            children: [],
          };
        } else {
          parentMap[typeId].label = item.text || item.name || typeId;
        }
      }
    });
    
    return Object.values(parentMap);
  };

  const handleToggleParent = (parentValue) => {
    const newExpanded = new Set(expandedParents);
    if (newExpanded.has(parentValue)) {
      newExpanded.delete(parentValue);
    } else {
      newExpanded.add(parentValue);
    }
    setExpandedParents(newExpanded);
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
            data.map((parent) => (
              <div key={parent.value} style={{ marginBottom: "0.5rem" }}>
                {/* Parent type */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "0.6rem 0.8rem",
                    cursor: parent.children.length > 0 ? "pointer" : "default",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      width: "100%",
                    }}
                  >
                    <div
                      role="button"
                      tabIndex={0}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        flex: 1,
                        cursor: "pointer",
                      }}
                      onClick={() => handleItemClick(parent.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          handleItemClick(parent.value);
                        }
                      }}
                    >
                      {parent.children.length > 0 && (
                        <Icon
                          name={
                            expandedParents.has(parent.value)
                              ? "caret down"
                              : "caret right"
                          }
                          style={{
                            marginRight: "0.5rem",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleParent(parent.value);
                          }}
                        />
                      )}
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
                            {parent.label}
                          </label>
                        }
                        checked={selectedType === parent.value}
                        style={{
                          marginLeft:
                            parent.children.length === 0 ? "1.5rem" : "0",
                        }}
                      />
                    </div>
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
                      {parent.count}
                    </Label>
                  </div>
                </div>

                {/* Child types */}
                {expandedParents.has(parent.value) &&
                  parent.children.length > 0 && (
                    <div style={{ marginLeft: "2rem" }}>
                      {parent.children.map((child) => (
                        <div
                          key={child.value}
                          role="button"
                          tabIndex={0}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            padding: "0.6rem 0.8rem",
                            cursor: "pointer",
                          }}
                          onClick={() =>
                            handleItemClick(child.value, parent.value)
                          }
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              handleItemClick(child.value, parent.value);
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
                                {child.label}
                              </label>
                            }
                            checked={selectedType === child.value}
                            style={{ flex: 1, marginRight: "0.5rem" }}
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
                            {child.count}
                          </Label>
                        </div>
                      ))}
                    </div>
                  )}
              </div>
            ))
          )}
        </div>
      </Card.Content>
    </Card>
  );
};

export default ResourceTypeFacet;
