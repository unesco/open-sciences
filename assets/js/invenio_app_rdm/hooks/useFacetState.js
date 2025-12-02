// Custom hook for managing facet state and URL synchronization
import { useState, useEffect, useCallback } from "react";

export const useFacetState = (queryField) => {
  const [selectedValue, setSelectedValue] = useState(null);

  // Get selected value from URL query parameters
  const getSelectedValueFromURL = useCallback(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const currentQuery = searchParams.get("q") || "";
    const escapedField = queryField.replace(/\./g, "\\.");
    const regex = new RegExp(`${escapedField}:"([^"]+)"`);
    const match = currentQuery.match(regex);
    return match ? match[1] : null;
  }, [queryField]);

  // Initialize from URL
  useEffect(() => {
    const urlValue = getSelectedValueFromURL();
    if (urlValue) {
      setSelectedValue(urlValue);
    }
  }, [getSelectedValueFromURL]);

  // Update URL with new filter value
  const updateURL = useCallback(
    (newValue) => {
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
    },
    [queryField]
  );

  return {
    selectedValue,
    setSelectedValue,
    updateURL,
  };
};
