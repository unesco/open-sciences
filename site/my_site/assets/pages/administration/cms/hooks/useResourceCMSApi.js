/**
 * Custom Hook for Resource-Driven CMS API interactions
 * Provides CRUD operations for content resources with loading/error states
 */
import { useState, useCallback } from "react";

/**
 * Custom hook for Resource-Driven CMS API operations
 * @param {string} baseEndpoint - Base API endpoint (default: /data/cms)
 */
export const useResourceCMSApi = (baseEndpoint = "/data/cms") => {
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

  // ========== Resources API ==========

  /**
   * List all available resource types
   * Returns resource definitions with schemas, labels, etc.
   */
  const listResources = useCallback(async () => {
    return fetchApi("/resources");
  }, [fetchApi]);

  /**
   * Get a single resource type definition
   * @param {string} resourceType - Resource type identifier
   */
  const getResource = useCallback(
    async (resourceType) => {
      return fetchApi(`/resources/${resourceType}`);
    },
    [fetchApi]
  );

  // ========== Content API ==========

  /**
   * List content for a resource type
   * @param {string} resourceType - Resource type identifier
   * @param {object} params - Query parameters (q, lang, published, page, size)
   */
  const listContent = useCallback(
    async (resourceType, params = {}) => {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          searchParams.append(key, value);
        }
      });
      const queryString = searchParams.toString();
      return fetchApi(
        `/content/${resourceType}${queryString ? `?${queryString}` : ""}`
      );
    },
    [fetchApi]
  );

  /**
   * Get content for a singleton resource type
   * @param {string} resourceType - Resource type identifier
   * @param {string} lang - Language code (default: en)
   */
  const getSingletonContent = useCallback(
    async (resourceType, lang = "en") => {
      return fetchApi(`/content/${resourceType}?lang=${lang}`);
    },
    [fetchApi]
  );

  /**
   * Get a single content item by ID
   * @param {string} resourceType - Resource type identifier
   * @param {number} id - Content ID
   */
  const getContent = useCallback(
    async (resourceType, id) => {
      return fetchApi(`/content/${resourceType}/${id}`);
    },
    [fetchApi]
  );

  /**
   * Create new content
   * @param {string} resourceType - Resource type identifier
   * @param {object} data - Content data (must include slug and data fields)
   */
  const createContent = useCallback(
    async (resourceType, data) => {
      return fetchApi(`/content/${resourceType}`, {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    [fetchApi]
  );

  /**
   * Update existing content
   * @param {string} resourceType - Resource type identifier
   * @param {number} id - Content ID
   * @param {object} data - Updated content data
   */
  const updateContent = useCallback(
    async (resourceType, id, data) => {
      return fetchApi(`/content/${resourceType}/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
    },
    [fetchApi]
  );

  /**
   * Delete content
   * @param {string} resourceType - Resource type identifier
   * @param {number} id - Content ID
   */
  const deleteContent = useCallback(
    async (resourceType, id) => {
      return fetchApi(`/content/${resourceType}/${id}`, {
        method: "DELETE",
      });
    },
    [fetchApi]
  );

  /**
   * Publish content
   * @param {string} resourceType - Resource type identifier
   * @param {number} id - Content ID
   */
  const publishContent = useCallback(
    async (resourceType, id) => {
      return fetchApi(`/content/${resourceType}/${id}/publish`, {
        method: "POST",
      });
    },
    [fetchApi]
  );

  /**
   * Unpublish content
   * @param {string} resourceType - Resource type identifier
   * @param {number} id - Content ID
   */
  const unpublishContent = useCallback(
    async (resourceType, id) => {
      return fetchApi(`/content/${resourceType}/${id}/unpublish`, {
        method: "POST",
      });
    },
    [fetchApi]
  );

  /**
   * Render content (get HTML or JSON output)
   * @param {string} resourceType - Resource type identifier
   * @param {string} slug - Content slug
   */
  const renderContent = useCallback(
    async (resourceType, slug) => {
      return fetchApi(`/content/${resourceType}/${slug}/render`);
    },
    [fetchApi]
  );

  return {
    loading,
    error,
    setError,
    // Resources
    listResources,
    getResource,
    // Content
    listContent,
    getSingletonContent,
    getContent,
    createContent,
    updateContent,
    deleteContent,
    publishContent,
    unpublishContent,
    renderContent,
  };
};
