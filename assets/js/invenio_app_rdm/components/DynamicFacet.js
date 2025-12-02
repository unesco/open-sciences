// Generic reusable facet component for InvenioRDM
// Can be used for Author, Subject, Affiliation, Funding, etc.
// Uses custom checkbox list with Semantic UI styling

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Card,
  Input,
  Label,
  Button,
  Checkbox,
  Icon,
  List,
  Loader,
} from "semantic-ui-react";
import PropTypes from "prop-types";
import _debounce from "lodash/debounce";

const DynamicFacet = ({
  label,
  apiField,
  queryField,
  placeholder,
  icon,
  maxResults,
}) => {
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [options, setOptions] = useState([]);
  const [selectedValue, setSelectedValue] = useState(null);
  const [visibleCount, setVisibleCount] = useState(10);
  const [isExpanded, setIsExpanded] = useState(false);

  const listRef = useRef(null);

  // Get selected value from URL query parameters
  const getSelectedValueFromURL = useCallback(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const currentQuery = searchParams.get("q") || "";
    const escapedField = queryField.replace(/\./g, "\\.");
    const regex = new RegExp(`${escapedField}:"([^"]+)"`);
    const match = currentQuery.match(regex);
    return match ? match[1] : null;
  }, [queryField]);

  // Fetch options from API
  const fetchOptions = useCallback(
    (query) => {
      setLoading(true);

      const url = `/data/search?field=${apiField}${
        query ? `&q=${encodeURIComponent(query)}` : ""
      }&size=${maxResults}&sort=count`;

      fetch(url)
        .then((response) => {
          if (!response.ok) throw new Error("Network response was not ok");
          return response.json();
        })
        .then((data) => {
          const results = data.results || [];
          const newOptions = results.map((item) => ({
            key: item.value,
            text: item.value,
            value: item.value,
            count: item.count,
          }));

          setOptions(newOptions);
          setLoading(false);
        })
        .catch((error) => {
          console.error(`Error fetching ${label}:`, error);
          setLoading(false);
        });
    },
    [apiField, maxResults, label]
  );

  // Debounced search
  const debouncedSearch = useRef(
    _debounce((query) => fetchOptions(query), 300)
  ).current;

  // Initialize component
  useEffect(() => {
    const urlValue = getSelectedValueFromURL();
    if (urlValue) {
      setSelectedValue(urlValue);
    }
    fetchOptions("");
  }, [getSelectedValueFromURL, fetchOptions]);

  // Handle search input change
  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    setVisibleCount(10);
    debouncedSearch(query);
  };

  // Handle checkbox selection
  const handleCheckboxChange = (value) => {
    const newValue = selectedValue === value ? null : value;
    setSelectedValue(newValue);

    // Build search query and redirect
    const searchParams = new URLSearchParams(window.location.search);
    const existingQuery = searchParams.get("q") || "";

    // Parse existing filters
    const filters = {};
    const filterRegex = /([^\s:]+(?:\.[^\s:]+)*):"([^"]+)"/g;
    let match;
    while ((match = filterRegex.exec(existingQuery)) !== null) {
      filters[match[1]] = match[2];
    }

    // Update or remove filter
    if (newValue) {
      filters[queryField] = newValue;
    } else {
      delete filters[queryField];
    }

    // Rebuild query
    const queryParts = Object.entries(filters).map(
      ([field, val]) => `${field}:"${val}"`
    );

    if (queryParts.length > 0) {
      searchParams.set("q", queryParts.join(" AND "));
    } else {
      searchParams.delete("q");
    }

    window.location.href = `/search?${searchParams.toString()}`;
  };

  // Clear filter
  const clearFilter = () => {
    setSelectedValue(null);
    const searchParams = new URLSearchParams(window.location.search);
    const existingQuery = searchParams.get("q") || "";

    const filters = {};
    const filterRegex = /([^\s:]+(?:\.[^\s:]+)*):"([^"]+)"/g;
    let match;
    while ((match = filterRegex.exec(existingQuery)) !== null) {
      filters[match[1]] = match[2];
    }

    delete filters[queryField];

    const queryParts = Object.entries(filters).map(
      ([field, val]) => `${field}:"${val}"`
    );

    if (queryParts.length > 0) {
      searchParams.set("q", queryParts.join(" AND "));
    } else {
      searchParams.delete("q");
    }

    window.location.href = `/search?${searchParams.toString()}`;
  };

  // Load more items
  const loadMore = () => {
    setVisibleCount((prev) => prev + 10);
  };

  // Handle focus/blur
  const handleFocus = () => setIsExpanded(true);
  const handleBlur = () => {
    setTimeout(() => setIsExpanded(false), 200);
  };

  const visibleOptions = options.slice(0, visibleCount);
  const hasMore = options.length > visibleCount;

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
            justifyContent: "space-between",
            marginBottom: "0.75rem",
            fontSize: "0.92rem",
            fontWeight: 600,
          }}
        >
          <span style={{ display: "flex", alignItems: "center" }}>
            {icon && (
              <Icon
                name={icon}
                style={{ marginRight: "8px", color: "#2185d0" }}
              />
            )}
            {label}
          </span>
          {selectedValue && (
            <Button
              basic
              compact
              size="mini"
              onClick={clearFilter}
              aria-label="Clear selection"
              title="Clear selection"
              style={{
                padding: "0.35rem 0.5rem",
                fontSize: "0.7rem",
                marginLeft: "0.5rem",
              }}
            >
              <Icon name="close" style={{ margin: 0, fontSize: "0.9rem" }} />
            </Button>
          )}
        </Card.Header>

        <Input
          fluid
          icon="search"
          iconPosition="left"
          placeholder={placeholder}
          value={searchQuery}
          onChange={handleSearchChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          loading={loading}
          style={{
            marginBottom: isExpanded || selectedValue ? "0.5rem" : "0",
          }}
          size="small"
        />

        {!isExpanded && selectedValue && !searchQuery && (
          <div style={{ marginTop: "0.5rem" }}>
            <Label
              color="blue"
              size="small"
              style={{ cursor: "pointer" }}
              onClick={clearFilter}
            >
              {selectedValue}
              <Icon name="delete" style={{ marginLeft: "0.3rem" }} />
            </Label>
          </div>
        )}

        {(isExpanded || (selectedValue && searchQuery)) && (
          <div
            ref={listRef}
            style={{
              maxHeight: "300px",
              overflowY: "auto",
              border: "1px solid rgba(34, 36, 38, 0.15)",
              borderRadius: "0.28571429rem",
              backgroundColor: "#fff",
              boxShadow: "0 2px 4px 0 rgba(34, 36, 38, 0.12)",
            }}
          >
            {loading && options.length === 0 ? (
              <div style={{ padding: "2rem", textAlign: "center" }}>
                <Loader active inline="centered" size="small" />
              </div>
            ) : options.length > 0 ? (
              <List
                divided
                selection
                verticalAlign="middle"
                style={{ margin: 0 }}
              >
                {visibleOptions.map((option) => (
                  <List.Item
                    key={option.key}
                    style={{
                      padding: "0.6rem 0.8rem",
                      cursor: "pointer",
                      transition: "background-color 0.1s ease",
                    }}
                    onClick={() => handleCheckboxChange(option.value)}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        width: "100%",
                      }}
                    >
                      <Checkbox
                        label={
                          <label
                            style={{
                              cursor: "pointer",
                              fontSize: "0.92rem",
                              color: "rgba(0, 0, 0, 0.87)",
                            }}
                          >
                            {option.text}
                          </label>
                        }
                        checked={selectedValue === option.value}
                        onChange={() => handleCheckboxChange(option.value)}
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
                        {option.count}
                      </Label>
                    </div>
                  </List.Item>
                ))}
              </List>
            ) : (
              <div
                style={{
                  padding: "1.5rem",
                  textAlign: "center",
                  color: "rgba(0, 0, 0, 0.4)",
                  fontSize: "0.9rem",
                }}
              >
                {searchQuery ? "No results found" : "Start typing to search"}
              </div>
            )}

            {hasMore && (
              <div
                style={{
                  padding: "0.5rem",
                  borderTop: "1px solid rgba(34, 36, 38, 0.1)",
                }}
              >
                <Button
                  basic
                  fluid
                  size="small"
                  onClick={loadMore}
                  style={{
                    textAlign: "center",
                    fontSize: "0.85rem",
                  }}
                >
                  <Icon name="angle down" />
                  Load More ({options.length - visibleCount} more)
                </Button>
              </div>
            )}
          </div>
        )}
      </Card.Content>
    </Card>
  );
};

DynamicFacet.propTypes = {
  label: PropTypes.string.isRequired,
  apiField: PropTypes.string.isRequired,
  queryField: PropTypes.string.isRequired,
  placeholder: PropTypes.string,
  icon: PropTypes.string,
  maxResults: PropTypes.number,
};

DynamicFacet.defaultProps = {
  placeholder: "Search...",
  icon: null,
  maxResults: 100,
};

export default DynamicFacet;
