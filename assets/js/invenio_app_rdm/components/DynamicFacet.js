// Refactored Dynamic Facet Component
// Uses custom hooks and separate components for better maintainability

import React, { useState, useRef } from "react";
import { Card, Input, Label, Icon, Loader } from "semantic-ui-react";
import PropTypes from "prop-types";

// Custom hooks
import { useFacetState } from "../hooks/useFacetState";
import { useFacetSearch } from "../hooks/useFacetSearch";

// Sub-components
import FacetHeader from "./facets/FacetHeader";
import FacetOptionsList from "./facets/FacetOptionsList";
import FacetPagination from "./facets/FacetPagination";

const DynamicFacet = ({
  label,
  apiField,
  queryField,
  placeholder,
  icon,
  pageSize,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const listRef = useRef(null);

  // Custom hooks for state management
  const { selectedValue, setSelectedValue, updateURL } =
    useFacetState(queryField);

  const {
    loading,
    searchQuery,
    options,
    currentPage,
    totalItems,
    totalPages,
    handleSearchChange,
    handlePageChange,
  } = useFacetSearch(apiField, pageSize);

  // Handle checkbox selection
  const handleSelect = (value) => {
    const newValue = selectedValue === value ? null : value;
    setSelectedValue(newValue);
    updateURL(newValue);
  };

  // Clear filter
  const handleClear = () => {
    setSelectedValue(null);
    updateURL(null);
  };

  // Handle focus (expand list) - prevent blur when clicking inside
  const handleFocus = () => setIsExpanded(true);

  // Handle blur (collapse list) - but not when clicking pagination
  const handleBlur = (e) => {
    // Check if the related target (what's being clicked) is inside the list
    if (listRef.current && listRef.current.contains(e.relatedTarget)) {
      return; // Don't collapse
    }
    setTimeout(() => setIsExpanded(false), 200);
  };

  // Prevent list collapse when interacting with it
  const handleListMouseDown = (e) => {
    e.preventDefault(); // Prevent input blur
  };

  return (
    <Card
      className="borderless facet"
      style={{ boxShadow: "none", border: "none" }}
    >
      <Card.Content style={{ padding: "0.65rem" }}>
        <FacetHeader
          label={label}
          icon={icon}
          selectedValue={selectedValue}
          onClear={handleClear}
        />

        <Input
          fluid
          icon="search"
          iconPosition="left"
          placeholder={placeholder}
          value={searchQuery}
          onChange={(e) => handleSearchChange(e.target.value)}
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
              onClick={handleClear}
            >
              {selectedValue}
              <Icon name="delete" style={{ marginLeft: "0.3rem" }} />
            </Label>
          </div>
        )}

        {(isExpanded || (selectedValue && searchQuery)) && (
          <div
            ref={listRef}
            onMouseDown={handleListMouseDown}
            role="listbox"
            aria-label={`${label} options`}
            tabIndex={0}
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
              <>
                <FacetOptionsList
                  options={options}
                  selectedValue={selectedValue}
                  loading={loading}
                  onSelect={handleSelect}
                />

                <FacetPagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  loading={loading}
                  onPageChange={handlePageChange}
                />

                {totalItems > 0 && (
                  <div
                    style={{
                      padding: "0.5rem",
                      textAlign: "center",
                      fontSize: "0.75rem",
                      color: "rgba(0, 0, 0, 0.5)",
                      borderTop:
                        totalPages > 1
                          ? "none"
                          : "1px solid rgba(34, 36, 38, 0.1)",
                      backgroundColor: "#fafafa",
                    }}
                  >
                    Showing {(currentPage - 1) * pageSize + 1}-
                    {Math.min(currentPage * pageSize, totalItems)} of{" "}
                    {totalItems} results
                  </div>
                )}
              </>
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
  pageSize: PropTypes.number,
};

DynamicFacet.defaultProps = {
  placeholder: "Search...",
  icon: null,
  pageSize: 10,
};

export default DynamicFacet;
