import React, { useState, useEffect } from "react";
import { Card, Checkbox, Popup, Icon } from "semantic-ui-react";

const OpenAccessToggleFacet = () => {
  const [isChecked, setIsChecked] = useState(false);

  // Get Open Access filter state from URL on mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const facetFilters = urlParams.getAll("f");

    // Check if is_open_access:true filter is present
    const hasOpenAccessFilter = facetFilters.some((f) =>
      f.startsWith("is_open_access:true")
    );

    setIsChecked(hasOpenAccessFilter);
  }, []);

  const handleToggle = () => {
    const newValue = !isChecked;
    setIsChecked(newValue);

    // Build new URL with or without Open Access filter
    const urlParams = new URLSearchParams(window.location.search);

    // Remove existing is_open_access filter
    const facetFilters = urlParams
      .getAll("f")
      .filter((f) => !f.startsWith("is_open_access:"));
    urlParams.delete("f");
    facetFilters.forEach((f) => urlParams.append("f", f));

    // Add new filter if checked
    if (newValue) {
      urlParams.append("f", "is_open_access:true");
    }

    // Reset to page 1 when filter changes
    urlParams.set("page", "1");

    // Navigate to new URL
    const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
    window.location.href = newUrl;
  };

  return (
    <Card
      className="borderless facet"
      style={{ boxShadow: "none", border: "none", width: "100%" }}
    >
      <Card.Content style={{ padding: "0.65rem", paddingRight: 0 }}>
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "flex-start",
            gap: "12px",
          }}
        >
          <span style={{ flexShrink: 0, lineHeight: 1 }}>
            <Checkbox toggle checked={isChecked} onChange={handleToggle} />
          </span>
          <span
            style={{
              color: "#212121",
              fontSize: "0.92rem",
              fontWeight: 600,
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            Open access
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
              content="Filter records that are open access publications"
              position="top center"
              size="small"
              inverted
            />
          </span>
        </div>
      </Card.Content>
    </Card>
  );
};

export default OpenAccessToggleFacet;
