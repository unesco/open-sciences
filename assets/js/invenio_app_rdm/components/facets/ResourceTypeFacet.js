import React, { useState, useEffect } from "react";
import {
  Card,
  Icon,
  Popup,
  Loader,
  Dimmer,
  Checkbox,
} from "semantic-ui-react";
import axios from "axios";

const ResourceTypeFacet = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState(null); // Single selection
  const [expandedParents, setExpandedParents] = useState(
    new Set(["publication"])
  ); // Expand by default

  // Parse URL to get current filter (single selection)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get("q") || "";

    // Extract resource_type filter from query string (take first match only)
    const typeMatch = query.match(/metadata\.resource_type\.id:"([^"]+)"/);
    if (typeMatch) {
      setSelectedType(typeMatch[1]);
    }
  }, []);

  // Fetch resource types from InvenioRDM aggregations
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch from InvenioRDM records API to get aggregations
        const response = await axios.get("/api/records", {
          params: {
            size: 1, // Minimum size required
          },
        });

        const aggregations = response.data.aggregations || {};
        const resourceTypeBuckets = aggregations.resource_type?.buckets || [];

        // Organize into hierarchical structure
        const hierarchy = organizeHierarchy(resourceTypeBuckets);
        setData(hierarchy);
      } catch (error) {
        console.error("Error fetching resource types:", error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

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

  const handleToggleParent = (parentValue) => {
    const newExpanded = new Set(expandedParents);
    if (newExpanded.has(parentValue)) {
      newExpanded.delete(parentValue);
    } else {
      newExpanded.add(parentValue);
    }
    setExpandedParents(newExpanded);
  };

  const handleItemClick = (typeValue) => {
    const urlParams = new URLSearchParams(window.location.search);
    const currentQuery = urlParams.get("q") || "";

    // Remove existing resource_type filters
    let newQuery = currentQuery
      .replace(/metadata\.resource_type\.id:"[^"]+"\s*(AND\s*)?/g, "")
      .trim();
    if (newQuery.endsWith("AND")) {
      newQuery = newQuery.slice(0, -3).trim();
    }

    // Toggle selection: if clicking the same item, deselect it
    const newSelectedType = selectedType === typeValue ? null : typeValue;

    // Build new query with updated selection
    if (newSelectedType) {
      const typeFilter = `metadata.resource_type.id:"${newSelectedType}"`;
      if (newQuery) {
        newQuery = `${newQuery} AND ${typeFilter}`;
      } else {
        newQuery = typeFilter;
      }
    }

    if (newQuery) {
      urlParams.set("q", newQuery);
    } else {
      urlParams.delete("q");
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
            color: "#2185d0",
            display: "flex",
            alignItems: "center",
            marginBottom: "0.75rem",
            fontSize: "0.92rem",
            fontWeight: 600,
          }}
        >
          <Icon
            name="file alternate"
            style={{ marginRight: "8px", color: "#2185d0" }}
          />
          <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            Resource Type
            <Popup
              trigger={
                <Icon
                  name="info circle"
                  style={{
                    fontSize: "0.85rem",
                    color: "rgba(0, 0, 0, 0.4)",
                    cursor: "help",
                    display: "flex",
                    alignItems: "center",
                  }}
                />
              }
              content="Filter by resource type (publication, dataset, etc.)"
              position="top center"
              size="small"
              inverted
            />
          </span>
        </Card.Header>
        {loading ? (
          <Dimmer active inverted>
            <Loader size="small" />
          </Dimmer>
        ) : (
          <div style={{ maxHeight: "300px", overflowY: "auto" }}>
            {data.length === 0 ? (
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
                      padding: "0.25rem 0",
                      cursor:
                        parent.children.length > 0 ? "pointer" : "default",
                    }}
                  >
                    {parent.children.length > 0 && (
                      <Icon
                        name={
                          expandedParents.has(parent.value)
                            ? "caret down"
                            : "caret right"
                        }
                        style={{ marginRight: "0.25rem", cursor: "pointer" }}
                        onClick={() => handleToggleParent(parent.value)}
                      />
                    )}
                    <Checkbox
                      radio
                      label={
                        <label style={{ cursor: "pointer" }}>
                          <strong>{parent.label}</strong>
                          <span
                            style={{ color: "#767676", marginLeft: "0.5rem" }}
                          >
                            ({parent.count})
                          </span>
                        </label>
                      }
                      checked={selectedType === parent.value}
                      onChange={() => handleItemClick(parent.value)}
                      style={{
                        marginLeft:
                          parent.children.length === 0 ? "1.5rem" : "0",
                      }}
                    />
                  </div>

                  {/* Child types */}
                  {expandedParents.has(parent.value) &&
                    parent.children.length > 0 && (
                      <div style={{ marginLeft: "2rem" }}>
                        {parent.children.map((child) => (
                          <div
                            key={child.value}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              padding: "0.25rem 0",
                            }}
                          >
                            <Checkbox
                              radio
                              label={
                                <label style={{ cursor: "pointer" }}>
                                  {child.label}
                                  <span
                                    style={{
                                      color: "#767676",
                                      marginLeft: "0.5rem",
                                    }}
                                  >
                                    ({child.count})
                                  </span>
                                </label>
                              }
                              checked={selectedType === child.value}
                              onChange={() => handleItemClick(child.value)}
                            />
                          </div>
                        ))}
                      </div>
                    )}
                </div>
              ))
            )}
          </div>
        )}
      </Card.Content>
    </Card>
  );
};

export default ResourceTypeFacet;
