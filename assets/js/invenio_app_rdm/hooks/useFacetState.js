// Custom hook for managing facet state and URL synchronization
import { useState, useEffect, useCallback } from "react";

export const useFacetState = (queryField, useFacetParameter = false, facetName = null) => {
  const [selectedValue, setSelectedValue] = useState(null);

  // Get selected value from URL query parameters
  const getSelectedValueFromURL = useCallback(() => {
    const searchParams = new URLSearchParams(window.location.search);
    
    // Check if using facet parameter (f=facetName:value)
    if (useFacetParameter && facetName) {
      const facetFilters = searchParams.getAll("f");
      for (const filter of facetFilters) {
        if (filter.startsWith(`${facetName}:`)) {
          return filter.substring(facetName.length + 1);
        }
      }
      return null;
    }
    
    // Otherwise use query parameter (q=field:"value")
    const currentQuery = searchParams.get("q") || "";
    const escapedField = queryField.replace(/\./g, "\\.");
    const regex = new RegExp(`${escapedField}:"([^"]+)"`);
    const match = currentQuery.match(regex);
    return match ? match[1] : null;
  }, [queryField, useFacetParameter, facetName]);

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
      
      // Handle facet parameter (f=facetName:value)
      if (useFacetParameter && facetName) {
        // Remove existing facet filter
        const facetFilters = searchParams.getAll("f").filter(
          (f) => !f.startsWith(`${facetName}:`)
        );
        searchParams.delete("f");
        facetFilters.forEach((f) => searchParams.append("f", f));
        
        // Add new facet filter if value provided
        if (newValue) {
          searchParams.append("f", `${facetName}:${newValue}`);
        }
      } else {
        // Handle query parameter (q=field:"value")
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
      }

      // Reset to page 1
      searchParams.set("page", "1");
      window.location.href = `/search?${searchParams.toString()}`;
    },
    [queryField, useFacetParameter, facetName]
  );

  return {
    selectedValue,
    setSelectedValue,
    updateURL,
  };
};
