import React, { useState, useEffect } from "react";
import { Card, Dropdown, Popup, Icon } from "semantic-ui-react";

// Filter patterns for URL parsing
const FILTER_PATTERNS = {
  funder: /custom_fields\.publication\\:funding_org:\*UNESCO\*/,
  author: /metadata\.creators\.affiliations\.name:\*UNESCO\*/,
};

// Filter query strings
const FILTER_QUERIES = {
  funder: "custom_fields.publication\\:funding_org:*UNESCO*",
  author: "metadata.creators.affiliations.name:*UNESCO*",
};

// Dropdown options
const OPTIONS = [
  { key: "none", value: "", text: "All records" },
  { key: "funder", value: "funder", text: "UNESCO as funder" },
  { key: "author", value: "author", text: "Author affiliated with UNESCO" },
];

const UnescoToggleFacet = () => {
  const [selectedValue, setSelectedValue] = useState("");

  // Initialize from URL on mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const existingQuery = urlParams.get("q") || "";

    // Check which filter is present (if any)
    if (FILTER_PATTERNS.funder.test(existingQuery)) {
      setSelectedValue("funder");
    } else if (FILTER_PATTERNS.author.test(existingQuery)) {
      setSelectedValue("author");
    } else {
      setSelectedValue("");
    }
  }, []);

  const handleChange = (e, { value }) => {
    const newValue = value;
    setSelectedValue(newValue);

    // Build new URL
    const urlParams = new URLSearchParams(window.location.search);
    let existingQuery = urlParams.get("q") || "";

    // Remove any existing UNESCO filters
    Object.values(FILTER_PATTERNS).forEach((pattern) => {
      if (pattern.test(existingQuery)) {
        existingQuery = existingQuery.replace(pattern, "").trim();
      }
    });

    // Clean up stray AND/OR operators
    existingQuery = existingQuery
      .replace(/^\s*AND\s+/i, "")
      .replace(/\s+AND\s*$/i, "")
      .replace(/\s+AND\s+AND\s+/gi, " AND ")
      .replace(/^\s*OR\s+/i, "")
      .replace(/\s+OR\s*$/i, "")
      .replace(/\s+OR\s+OR\s+/gi, " OR ")
      .trim();

    // Add new filter if selected
    if (newValue && FILTER_QUERIES[newValue]) {
      const filterQuery = FILTER_QUERIES[newValue];
      if (existingQuery) {
        existingQuery = existingQuery + " AND " + filterQuery;
      } else {
        existingQuery = filterQuery;
      }
    }

    // Build new query string
    const newParams = new URLSearchParams();

    // Preserve all other parameters
    urlParams.forEach((val, key) => {
      if (key !== "q") {
        newParams.append(key, val);
      }
    });

    // Add updated query if not empty
    if (existingQuery && existingQuery.trim()) {
      newParams.set("q", existingQuery);
    }

    // Reset to page 1 when filter changes
    newParams.set("page", "1");

    // Navigate to new URL
    const newUrl = `${window.location.pathname}?${newParams.toString()}`;
    window.location.href = newUrl;
  };

  return (
    <Card
      className="borderless facet"
      style={{ boxShadow: "none", border: "none", width: "100%" }}
    >
      <Card.Content style={{ padding: "0.65rem" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-start",
            marginBottom: "0.75rem",
            gap: "4px",
          }}
        >
          <span
            style={{
              color: "#212121",
              fontSize: "0.92rem",
              fontWeight: 600,
            }}
          >
            Type of UNESCO involvement
          </span>
          <Popup
            trigger={
              <Icon
                name="info circle"
                style={{
                  fontSize: "0.85rem",
                  color: "rgba(0, 0, 0, 0.4)",
                  cursor: "help",
                  margin: 0,
                  lineHeight: 1,
                  verticalAlign: "middle",
                }}
              />
            }
            content="Filter records by UNESCO involvement: as a funder or through author affiliation"
            position="top center"
            size="small"
            inverted
          />
        </div>
        <Dropdown
          placeholder="Select filter..."
          fluid
          selection
          clearable
          options={OPTIONS}
          value={selectedValue}
          onChange={handleChange}
          style={{ fontSize: "0.9rem" }}
        />
      </Card.Content>
    </Card>
  );
};

export default UnescoToggleFacet;
