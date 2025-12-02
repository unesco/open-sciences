// Custom hook for managing facet search and pagination
import { useState, useCallback, useRef, useEffect } from "react";
import _debounce from "lodash/debounce";

export const useFacetSearch = (apiField, pageSize = 10) => {
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [options, setOptions] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  // Fetch options from API with pagination
  const fetchOptions = useCallback(
    (query, page = 1) => {
      setLoading(true);

      const url = `/data/search?field=${apiField}${
        query ? `&q=${encodeURIComponent(query)}` : ""
      }&page=${page}&size=${pageSize}&sort=count`;

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
          setTotalItems(data.total || 0);
          setTotalPages(Math.ceil((data.total || 0) / pageSize));
          setCurrentPage(page);
          setLoading(false);
        })
        .catch((error) => {
          console.error(`Error fetching facet data:`, error);
          setLoading(false);
        });
    },
    [apiField, pageSize]
  );

  // Debounced search (resets to page 1)
  const debouncedSearch = useRef(
    _debounce((query) => {
      setCurrentPage(1);
      fetchOptions(query, 1);
    }, 300)
  ).current;

  // Initialize - fetch initial data
  useEffect(() => {
    fetchOptions("", 1);
  }, [fetchOptions]);

  // Handle search input change
  const handleSearchChange = (query) => {
    setSearchQuery(query);
    debouncedSearch(query);
  };

  // Handle page change
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages && newPage !== currentPage) {
      fetchOptions(searchQuery, newPage);
    }
  };

  return {
    loading,
    searchQuery,
    options,
    currentPage,
    totalItems,
    totalPages,
    handleSearchChange,
    handlePageChange,
  };
};
