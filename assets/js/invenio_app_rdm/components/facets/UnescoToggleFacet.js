import React, { useState, useEffect } from "react";
import { Card, Checkbox, Icon, Popup } from "semantic-ui-react";

const UnescoToggleFacet = () => {
  const [isChecked, setIsChecked] = useState(false);

  // Get UNESCO filter state from URL on mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const existingQuery = urlParams.get("q") || "";

    // Check if UNESCO filter is present in the query
    const unescoPattern =
      /\(metadata\.creators\.affiliations\.name:\*UNESCO\*\s+OR\s+custom_fields\.publication\\:funding_org:\*UNESCO\*\)/;
    const hasUnescoFilter = unescoPattern.test(existingQuery);

    setIsChecked(hasUnescoFilter);
  }, []);

  const handleToggle = () => {
    const newValue = !isChecked;
    setIsChecked(newValue);

    // Build new URL with or without UNESCO filter
    const urlParams = new URLSearchParams(window.location.search);
    let existingQuery = urlParams.get("q") || "";

    const unescoPattern =
      /\(metadata\.creators\.affiliations\.name:\*UNESCO\*\s+OR\s+custom_fields\.publication\\:funding_org:\*UNESCO\*\)/;
    const unescoFilter =
      "(metadata.creators.affiliations.name:*UNESCO* OR custom_fields.publication\\:funding_org:*UNESCO*)";

    if (newValue) {
      // Add UNESCO filter
      if (existingQuery && !unescoPattern.test(existingQuery)) {
        existingQuery = existingQuery + " AND " + unescoFilter;
      } else if (!existingQuery) {
        existingQuery = unescoFilter;
      }
    } else {
      // Remove UNESCO filter
      if (unescoPattern.test(existingQuery)) {
        existingQuery = existingQuery.replace(unescoPattern, "").trim();
        // Clean up stray AND operators
        existingQuery = existingQuery
          .replace(/^\s*AND\s+/, "")
          .replace(/\s+AND\s*$/, "")
          .replace(/\s+AND\s+AND\s+/g, " AND ");
      }
    }

    // Build new query string
    const newParams = new URLSearchParams();

    // Preserve all other parameters
    urlParams.forEach((value, key) => {
      if (key !== "q") {
        newParams.append(key, value);
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
            name="university"
            style={{ marginRight: "8px", color: "#2185d0" }}
          />
          <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            UNESCO
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
              content="Filter records that have UNESCO affiliation or UNESCO funding organization"
              position="top center"
              size="small"
              inverted
            />
          </span>
        </Card.Header>
        <div style={{ marginTop: "0.5rem" }}>
          <Checkbox toggle checked={isChecked} onChange={handleToggle} />
        </div>
      </Card.Content>
    </Card>
  );
};

export default UnescoToggleFacet;
