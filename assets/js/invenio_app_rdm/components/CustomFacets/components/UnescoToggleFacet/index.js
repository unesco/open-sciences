import React, { useState, useEffect } from "react";
import { Card, Dropdown, Popup, Icon } from "semantic-ui-react";

// Base field for all UNESCO relation filters
const RELATION_FIELD = "custom_fields.publication\\:unesco_relation";

// Filter patterns for URL parsing
const FILTER_PATTERNS = {
  funded:     new RegExp(`${RELATION_FIELD.replace(/\\/g, "\\\\")}:"Funded by UNESCO"`),
  published:  new RegExp(`${RELATION_FIELD.replace(/\\/g, "\\\\")}:"Published by UNESCO"`),
  affiliated: new RegExp(`${RELATION_FIELD.replace(/\\/g, "\\\\")}:"UNESCO Affiliated Author"`),
  collective: new RegExp(`${RELATION_FIELD.replace(/\\/g, "\\\\")}:"UNESCO Collective Author"`),
};

// Filter query strings
const FILTER_QUERIES = {
  funded:     `${RELATION_FIELD}:"Funded by UNESCO"`,
  published:  `${RELATION_FIELD}:"Published by UNESCO"`,
  affiliated: `${RELATION_FIELD}:"UNESCO Affiliated Author"`,
  collective: `${RELATION_FIELD}:"UNESCO Collective Author"`,
};

// Dropdown options
const OPTIONS = [
  { key: "none",       value: "",           text: "All records" },
  { key: "funded",     value: "funded",     text: "Supported/funded by UNESCO" },
  { key: "published",  value: "published",  text: "Published by UNESCO" },
  { key: "affiliated", value: "affiliated", text: "Authored by individuals affiliated with UNESCO" },
  { key: "collective", value: "collective", text: "Produced by UNESCO as collective author" },
];

const UnescoToggleFacet = () => {
  const [selectedValue, setSelectedValue] = useState("");

  // Initialize from URL on mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const existingQuery = urlParams.get("q") || "";

    // Check which filter is present (if any)
    const match = Object.keys(FILTER_PATTERNS).find((key) =>
      FILTER_PATTERNS[key].test(existingQuery)
    );
    setSelectedValue(match || "");
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
            content="Filter records by type of UNESCO involvement: funded by, published by, affiliated author, or UNESCO as collective author"
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
