/**
 * ContentList Component
 * Lists content items for a specific resource type with elegant UI
 * Supports pagination and filtering for collection resources
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import PropTypes from "prop-types";
import {
  Table,
  Button,
  Loader,
  Message,
  Icon,
  Label,
  Header,
  Segment,
  Popup,
  Card,
  Grid,
  Input,
  Pagination,
  Dropdown,
} from "semantic-ui-react";
import { useResourceCMSApi, useDebounce } from "../../hooks";
import ConfirmModal from "../ConfirmModal";

/**
 * ContentList - Shows content items for a resource type
 */
export const ContentList = ({
  resourceType,
  resourceDefinition,
  onEdit,
  onBack,
  refreshKey,
}) => {
  const {
    listContent,
    deleteContent,
    publishContent,
    unpublishContent,
    loading,
    error,
  } = useResourceCMSApi();

  const [items, setItems] = useState([]);
  const [deleteModal, setDeleteModal] = useState({ open: false, item: null });
  
  // Pagination state
  const [pagination, setPagination] = useState({
    page: 1,
    size: 10,
    total: 0,
    pages: 1,
  });
  
  // Filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState("created");
  const [sortDirection, setSortDirection] = useState("desc");
  
  // Debounce search query to avoid too many API calls
  const debouncedSearch = useDebounce(searchQuery, 300);
  
  // Track if this is initial load
  const isInitialLoad = useRef(true);

  // Fetch content with pagination and filters
  const fetchContent = useCallback(async (params = {}) => {
    try {
      const queryParams = {
        page: params.page || pagination.page,
        size: params.size || pagination.size,
        q: params.q !== undefined ? params.q : debouncedSearch,
        sort: params.sort || sortField,
        sort_direction: params.sort_direction || sortDirection,
      };
      
      const result = await listContent(resourceType, queryParams);
      
      if (result.is_singleton) {
        setItems(result.content ? [result.content] : []);
        setPagination({ page: 1, size: 1, total: result.content ? 1 : 0, pages: 1 });
      } else {
        setItems(result.hits || []);
        setPagination({
          page: result.page || 1,
          size: result.size || 10,
          total: result.total || 0,
          pages: result.pages || 1,
        });
      }
    } catch (err) {
      console.error("Error fetching content:", err);
    }
  }, [listContent, resourceType, pagination.page, pagination.size, debouncedSearch, sortField, sortDirection]);

  // Initial fetch
  useEffect(() => {
    if (isInitialLoad.current) {
      isInitialLoad.current = false;
      fetchContent({ page: 1 });
    }
  }, []);
  
  // Refetch on refresh key change
  useEffect(() => {
    if (!isInitialLoad.current) {
      fetchContent({ page: 1 });
    }
  }, [refreshKey]);
  
  // Refetch when search query changes (debounced)
  useEffect(() => {
    if (!isInitialLoad.current) {
      fetchContent({ page: 1, q: debouncedSearch });
    }
  }, [debouncedSearch]);

  // Handle page change
  const handlePageChange = (e, { activePage }) => {
    fetchContent({ page: activePage });
  };
  
  // Handle sort change
  const handleSortChange = (field) => {
    const newDirection = sortField === field && sortDirection === "desc" ? "asc" : "desc";
    setSortField(field);
    setSortDirection(newDirection);
    fetchContent({ page: 1, sort: field, sort_direction: newDirection });
  };
  
  // Handle page size change
  const handleSizeChange = (e, { value }) => {
    fetchContent({ page: 1, size: value });
  };

  // Handle delete
  const handleDelete = async () => {
    if (!deleteModal.item) return;
    try {
      await deleteContent(resourceType, deleteModal.item.id);
      setDeleteModal({ open: false, item: null });
      fetchContent({ page: pagination.page });
    } catch (err) {
      console.error("Error deleting content:", err);
    }
  };

  // Handle publish/unpublish
  const handleTogglePublish = async (item) => {
    try {
      if (item.is_published) {
        await unpublishContent(resourceType, item.id);
      } else {
        await publishContent(resourceType, item.id);
      }
      fetchContent({ page: pagination.page });
    } catch (err) {
      console.error("Error toggling publish:", err);
    }
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Get title from content data
  const getContentTitle = (item) => {
    const data = item.data || {};
    return (
      data.title ||
      data.name ||
      data.section_title ||
      data.heading ||
      item.slug ||
      `Content #${item.id}`
    );
  };

  // Get icon for resource type
  const getResourceIcon = () => {
    const icons = {
      header: "window maximize outline",
      footer: "window minimize outline",
      homepage_hero: "image outline",
      homepage_highlights: "star outline",
      homepage_partners: "handshake outline",
      homepage_infographics: "chart bar outline",
      privacy_policy: "shield alternate",
      plain_language_summary: "file text outline",
      static_page: "file alternate outline",
    };
    return icons[resourceType] || "file outline";
  };

  if (loading && items.length === 0) {
    return (
      <Segment placeholder style={{ minHeight: "200px" }}>
        <Loader active size="large">
          Loading content...
        </Loader>
      </Segment>
    );
  }

  const isSingleton = resourceDefinition?.is_singleton;

  // Render singleton view (single card)
  if (isSingleton) {
    const item = items[0];
    return (
      <div className="content-list">
        {/* Header */}
        <Segment
          style={{
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color: "white",
            marginBottom: "1.5rem",
            borderRadius: "8px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center" }}>
              <Icon
                name={getResourceIcon()}
                size="big"
                style={{ marginRight: "1rem", opacity: 0.9 }}
              />
              <div>
                <Header
                  as="h2"
                  style={{ color: "white", margin: 0, marginBottom: "0.25rem" }}
                >
                  {resourceDefinition?.label || resourceType}
                </Header>
                <p style={{ margin: 0, opacity: 0.85, fontSize: "0.95rem" }}>
                  {resourceDefinition?.description}
                </p>
              </div>
            </div>
            <Label
              size="small"
              style={{
                background: "rgba(255,255,255,0.2)",
                color: "white",
                border: "1px solid rgba(255,255,255,0.3)",
              }}
            >
              <Icon name="cube" /> Singleton
            </Label>
          </div>
        </Segment>

        {error && (
          <Message negative icon>
            <Icon name="warning circle" />
            <Message.Content>
              <Message.Header>Error</Message.Header>
              <p>{error}</p>
            </Message.Content>
          </Message>
        )}

        {item ? (
          <Segment raised style={{ borderRadius: "8px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
              }}
            >
              <div>
                <Header as="h3" style={{ marginBottom: "0.5rem" }}>
                  <Icon name="file text" color="blue" />
                  {getContentTitle(item)}
                </Header>
                <div
                  style={{
                    color: "#666",
                    fontSize: "0.9rem",
                    marginBottom: "1rem",
                  }}
                >
                  <span style={{ marginRight: "1.5rem" }}>
                    <Icon name="globe" /> {item.lang || "en"}
                  </span>
                  <span style={{ marginRight: "1.5rem" }}>
                    <Icon name="clock outline" /> {formatDate(item.updated)}
                  </span>
                  <Label
                    size="tiny"
                    color={item.is_published ? "green" : "grey"}
                  >
                    <Icon name={item.is_published ? "check" : "clock"} />
                    {item.is_published ? "Published" : "Draft"}
                  </Label>
                </div>
              </div>
            </div>
            <div
              style={{
                borderTop: "1px solid #eee",
                paddingTop: "1rem",
                marginTop: "0.5rem",
              }}
            >
              <Button primary onClick={() => onEdit(item)}>
                <Icon name="edit" /> Edit Content
              </Button>
              <Button
                basic
                color={item.is_published ? "grey" : "green"}
                onClick={() => handleTogglePublish(item)}
              >
                <Icon name={item.is_published ? "eye slash" : "eye"} />
                {item.is_published ? "Unpublish" : "Publish"}
              </Button>
            </div>
          </Segment>
        ) : (
          <Segment placeholder style={{ borderRadius: "8px" }}>
            <Header icon>
              <Icon name="file outline" color="grey" />
              No content configured yet
            </Header>
            <p
              style={{
                color: "#888",
                textAlign: "center",
                marginBottom: "1.5rem",
              }}
            >
              Create content for this singleton resource to get started.
            </p>
            <Button
              primary
              size="large"
              onClick={() => onEdit(null)}
              style={{
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              }}
            >
              <Icon name="plus" /> Create Content
            </Button>
          </Segment>
        )}

        <ConfirmModal
          open={deleteModal.open}
          title="Delete Content"
          message={`Are you sure you want to delete "${getContentTitle(
            deleteModal.item || {}
          )}"?`}
          confirmText="Delete"
          confirmColor="red"
          onConfirm={handleDelete}
          onCancel={() => setDeleteModal({ open: false, item: null })}
        />
      </div>
    );
  }

  // Page size options
  const pageSizeOptions = [
    { key: 10, text: "10 per page", value: 10 },
    { key: 25, text: "25 per page", value: 25 },
    { key: 50, text: "50 per page", value: 50 },
    { key: 100, text: "100 per page", value: 100 },
  ];

  // Sort icon helper
  const getSortIcon = (field) => {
    if (sortField !== field) return null;
    return sortDirection === "asc" ? "sort up" : "sort down";
  };

  // Render collection view (table)
  return (
    <div className="content-list">
      {/* Header */}
      <Segment
        style={{
          background: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
          color: "white",
          marginBottom: "1.5rem",
          borderRadius: "8px",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center" }}>
            <Icon
              name={getResourceIcon()}
              size="big"
              style={{ marginRight: "1rem", opacity: 0.9 }}
            />
            <div>
              <Header
                as="h2"
                style={{ color: "white", margin: 0, marginBottom: "0.25rem" }}
              >
                {resourceDefinition?.label || resourceType}
              </Header>
              <p style={{ margin: 0, opacity: 0.85, fontSize: "0.95rem" }}>
                {resourceDefinition?.description}
              </p>
            </div>
          </div>
          <Button
            inverted
            onClick={() => onEdit(null)}
            style={{ background: "rgba(255,255,255,0.15)" }}
          >
            <Icon name="plus" /> Add New
          </Button>
        </div>
      </Segment>

      {/* Search and Filter Toolbar */}
      <Segment style={{ marginBottom: "1rem", padding: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          <Input
            icon="search"
            placeholder="Search by title or slug..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ flex: "1", minWidth: "200px", maxWidth: "400px" }}
          />
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ color: "#666", fontSize: "0.9rem" }}>Show:</span>
            <Dropdown
              selection
              compact
              options={pageSizeOptions}
              value={pagination.size}
              onChange={handleSizeChange}
              style={{ minWidth: "130px" }}
            />
          </div>
          <div style={{ marginLeft: "auto", color: "#666", fontSize: "0.9rem" }}>
            {pagination.total > 0 ? (
              <>
                Showing {((pagination.page - 1) * pagination.size) + 1} - {Math.min(pagination.page * pagination.size, pagination.total)} of {pagination.total} items
              </>
            ) : (
              "No items found"
            )}
          </div>
        </div>
      </Segment>

      {error && (
        <Message negative icon>
          <Icon name="warning circle" />
          <Message.Content>
            <Message.Header>Error</Message.Header>
            <p>{error}</p>
          </Message.Content>
        </Message>
      )}

      {loading && items.length === 0 ? (
        <Segment placeholder style={{ minHeight: "200px" }}>
          <Loader active size="large">Loading content...</Loader>
        </Segment>
      ) : items.length > 0 ? (
        <>
          <Segment
            raised
            style={{ borderRadius: "8px", padding: 0, overflow: "hidden" }}
          >
            <Table basic="very" selectable sortable style={{ margin: 0 }}>
              <Table.Header>
                <Table.Row style={{ background: "#f9fafb" }}>
                  <Table.HeaderCell 
                    style={{ padding: "1rem", cursor: "pointer" }}
                    onClick={() => handleSortChange("slug")}
                  >
                    Title
                    {getSortIcon("slug") && <Icon name={getSortIcon("slug")} style={{ marginLeft: "0.5rem" }} />}
                  </Table.HeaderCell>
                  <Table.HeaderCell width={2} textAlign="center">
                    Lang
                  </Table.HeaderCell>
                  <Table.HeaderCell width={2} textAlign="center">
                    Status
                  </Table.HeaderCell>
                  <Table.HeaderCell 
                    width={3}
                    style={{ cursor: "pointer" }}
                    onClick={() => handleSortChange("updated")}
                  >
                    Updated
                    {getSortIcon("updated") && <Icon name={getSortIcon("updated")} style={{ marginLeft: "0.5rem" }} />}
                  </Table.HeaderCell>
                  <Table.HeaderCell 
                    width={3}
                    style={{ cursor: "pointer" }}
                    onClick={() => handleSortChange("created")}
                  >
                    Created
                    {getSortIcon("created") && <Icon name={getSortIcon("created")} style={{ marginLeft: "0.5rem" }} />}
                  </Table.HeaderCell>
                  <Table.HeaderCell width={2} textAlign="center">
                    Actions
                  </Table.HeaderCell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
              {items.map((item) => (
                <Table.Row key={item.id} style={{ cursor: "pointer" }}>
                  <Table.Cell style={{ padding: "1rem" }}>
                    <div style={{ fontWeight: 600, color: "#333" }}>
                      {getContentTitle(item)}
                    </div>
                    <div
                      style={{
                        color: "#999",
                        fontSize: "0.85rem",
                        marginTop: "0.25rem",
                      }}
                    >
                      <Icon name="linkify" size="small" /> /{item.slug}
                    </div>
                  </Table.Cell>
                  <Table.Cell textAlign="center">
                    <Label size="small" basic>
                      {item.lang || "en"}
                    </Label>
                  </Table.Cell>
                  <Table.Cell textAlign="center">
                    <Label
                      size="small"
                      color={item.is_published ? "green" : "grey"}
                    >
                      <Icon
                        name={item.is_published ? "check" : "clock outline"}
                      />
                      {item.is_published ? "Live" : "Draft"}
                    </Label>
                  </Table.Cell>
                  <Table.Cell style={{ color: "#666", fontSize: "0.9rem" }}>
                    {formatDate(item.updated)}
                  </Table.Cell>
                  <Table.Cell style={{ color: "#666", fontSize: "0.9rem" }}>
                    {formatDate(item.created)}
                  </Table.Cell>
                  <Table.Cell textAlign="center">
                    <Button.Group size="small" basic>
                      <Popup
                        content="Edit"
                        trigger={
                          <Button icon="edit" onClick={() => onEdit(item)} />
                        }
                      />
                      <Popup
                        content={item.is_published ? "Unpublish" : "Publish"}
                        trigger={
                          <Button
                            icon={item.is_published ? "eye slash" : "eye"}
                            onClick={() => handleTogglePublish(item)}
                          />
                        }
                      />
                      <Popup
                        content="Delete"
                        trigger={
                          <Button
                            icon="trash"
                            color="red"
                            onClick={() => setDeleteModal({ open: true, item })}
                          />
                        }
                      />
                    </Button.Group>
                  </Table.Cell>
                </Table.Row>
              ))}
              </Table.Body>
            </Table>
          </Segment>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div style={{ display: "flex", justifyContent: "center", marginTop: "1.5rem" }}>
              <Pagination
                activePage={pagination.page}
                totalPages={pagination.pages}
                onPageChange={handlePageChange}
                ellipsisItem={{ content: <Icon name="ellipsis horizontal" />, icon: true }}
                firstItem={{ content: <Icon name="angle double left" />, icon: true }}
                lastItem={{ content: <Icon name="angle double right" />, icon: true }}
                prevItem={{ content: <Icon name="angle left" />, icon: true }}
                nextItem={{ content: <Icon name="angle right" />, icon: true }}
              />
            </div>
          )}
        </>
      ) : (
        <Segment placeholder style={{ borderRadius: "8px" }}>
          <Header icon>
            <Icon name="folder open outline" color="grey" />
            {searchQuery ? "No matching items" : "No content items yet"}
          </Header>
          <p
            style={{
              color: "#888",
              textAlign: "center",
              marginBottom: "1.5rem",
            }}
          >
            {searchQuery 
              ? `No items match "${searchQuery}". Try a different search term.`
              : `Get started by creating your first ${resourceDefinition?.label || resourceType}.`
            }
          </p>
          {!searchQuery && (
            <Button
              primary
              size="large"
              onClick={() => onEdit(null)}
              style={{
                background: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
              }}
            >
              <Icon name="plus" /> Create First Item
            </Button>
          )}
          {searchQuery && (
            <Button
              basic
              onClick={() => setSearchQuery("")}
            >
              <Icon name="times" /> Clear Search
            </Button>
          )}
        </Segment>
      )}

      <ConfirmModal
        open={deleteModal.open}
        title="Delete Content"
        message={`Are you sure you want to delete "${getContentTitle(
          deleteModal.item || {}
        )}"? This action cannot be undone.`}
        confirmText="Delete"
        confirmColor="red"
        onConfirm={handleDelete}
        onCancel={() => setDeleteModal({ open: false, item: null })}
      />
    </div>
  );
};

ContentList.propTypes = {
  resourceType: PropTypes.string.isRequired,
  resourceDefinition: PropTypes.object,
  onEdit: PropTypes.func.isRequired,
  onBack: PropTypes.func.isRequired,
  refreshKey: PropTypes.number,
};

ContentList.defaultProps = {
  resourceDefinition: null,
  refreshKey: 0,
};

export default ContentList;
