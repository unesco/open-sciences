// Custom Hook for CMS API interactions
import { useState, useCallback } from "react";

/**
 * Custom hook for CMS API operations
 * Provides CRUD operations for pages and categories with loading/error states
 */
export const useCMSApi = (baseEndpoint = "/data/cms") => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Generic fetch wrapper with error handling
   */
  const fetchApi = useCallback(
    async (url, options = {}) => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${baseEndpoint}${url}`, {
          headers: {
            "Content-Type": "application/json",
            ...options.headers,
          },
          ...options,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || `HTTP error ${response.status}`);
        }

        const data = await response.json();
        return data;
      } catch (err) {
        setError(err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [baseEndpoint]
  );

  // ========== Pages API ==========

  /**
   * List/search pages with filters
   */
  const listPages = useCallback(
    async (params = {}) => {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          searchParams.append(key, value);
        }
      });
      const queryString = searchParams.toString();
      return fetchApi(`/pages${queryString ? `?${queryString}` : ""}`);
    },
    [fetchApi]
  );

  /**
   * Get a single page by ID
   */
  const getPage = useCallback(
    async (id) => {
      return fetchApi(`/pages/${id}`);
    },
    [fetchApi]
  );

  /**
   * Create a new page
   */
  const createPage = useCallback(
    async (data) => {
      return fetchApi("/pages", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    [fetchApi]
  );

  /**
   * Update an existing page
   */
  const updatePage = useCallback(
    async (id, data) => {
      return fetchApi(`/pages/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
    },
    [fetchApi]
  );

  /**
   * Delete a page
   */
  const deletePage = useCallback(
    async (id) => {
      return fetchApi(`/pages/${id}`, {
        method: "DELETE",
      });
    },
    [fetchApi]
  );

  /**
   * Publish a page
   */
  const publishPage = useCallback(
    async (id) => {
      return fetchApi(`/pages/${id}/publish`, {
        method: "POST",
      });
    },
    [fetchApi]
  );

  /**
   * Unpublish a page
   */
  const unpublishPage = useCallback(
    async (id) => {
      return fetchApi(`/pages/${id}/unpublish`, {
        method: "POST",
      });
    },
    [fetchApi]
  );

  // ========== Categories API ==========

  /**
   * List/search categories
   */
  const listCategories = useCallback(
    async (params = {}) => {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          searchParams.append(key, value);
        }
      });
      const queryString = searchParams.toString();
      return fetchApi(`/categories${queryString ? `?${queryString}` : ""}`);
    },
    [fetchApi]
  );

  /**
   * Get a single category by ID
   */
  const getCategory = useCallback(
    async (id) => {
      return fetchApi(`/categories/${id}`);
    },
    [fetchApi]
  );

  /**
   * Create a new category
   */
  const createCategory = useCallback(
    async (data) => {
      return fetchApi("/categories", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    [fetchApi]
  );

  /**
   * Update an existing category
   */
  const updateCategory = useCallback(
    async (id, data) => {
      return fetchApi(`/categories/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
    },
    [fetchApi]
  );

  /**
   * Delete a category
   */
  const deleteCategory = useCallback(
    async (id) => {
      return fetchApi(`/categories/${id}`, {
        method: "DELETE",
      });
    },
    [fetchApi]
  );

  return {
    loading,
    error,
    setError,
    // Pages
    listPages,
    getPage,
    createPage,
    updatePage,
    deletePage,
    publishPage,
    unpublishPage,
    // Categories
    listCategories,
    getCategory,
    createCategory,
    updateCategory,
    deleteCategory,
  };
};
