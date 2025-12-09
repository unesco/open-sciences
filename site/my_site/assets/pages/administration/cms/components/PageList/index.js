// PageList Component
// Displays a list of CMS pages with search, filters, and pagination

import React, { useState, useEffect, useCallback } from "react";
import {
  Table,
  Button,
  Input,
  Icon,
  Label,
  Dropdown,
  Pagination,
  Segment,
  Message,
  Popup,
  Loader,
  Dimmer,
} from "semantic-ui-react";
import PropTypes from "prop-types";

import { useCMSApi } from "../../hooks/useCMSApi";
import { useDebounce } from "../../hooks/useDebounce";
import ConfirmModal from "../ConfirmModal";

const PageList = ({ onEdit, onRefresh }) => {
  // State
  const [pages, setPages] = useState([]);
  const [categories, setCategories] = useState([]);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [langFilter, setLangFilter] = useState("");
  const [publishedFilter, setPublishedFilter] = useState("");
  const [sortField, setSortField] = useState("created");
  const [sortDirection, setSortDirection] = useState("desc");

  // Modal state
  const [deleteModal, setDeleteModal] = useState({ open: false, page: null });
  const [actionLoading, setActionLoading] = useState(false);

  // Debounced search
  const debouncedSearch = useDebounce(searchQuery, 300);

  // API hook
  const {
    loading,
    error,
    listPages,
    deletePage,
    publishPage,
    unpublishPage,
    listCategories,
  } = useCMSApi();

  // Fetch pages
  const fetchPages = useCallback(async () => {
    try {
      const params = {
        page: currentPage,
        size: 10,
        sort: sortField,
        sort_direction: sortDirection,
      };

      if (debouncedSearch) params.q = debouncedSearch;
      if (categoryFilter) params.category_id = categoryFilter;
      if (langFilter) params.lang = langFilter;
      if (publishedFilter === "published") params.published_only = true;

      const result = await listPages(params);
      setPages(result.hits || []);
      setTotalPages(result.pages || 1);
      setTotalItems(result.total || 0);
    } catch (err) {
      console.error("Error fetching pages:", err);
    }
  }, [
    currentPage,
    debouncedSearch,
    categoryFilter,
    langFilter,
    publishedFilter,
    sortField,
    sortDirection,
    listPages,
  ]);

  // Fetch categories for filter dropdown
  const fetchCategories = useCallback(async () => {
    try {
      const result = await listCategories({ size: 100 });
      setCategories(result.hits || []);
    } catch (err) {
      console.error("Error fetching categories:", err);
    }
  }, [listCategories]);

  // Initial load and refresh
  useEffect(() => {
    fetchPages();
  }, [fetchPages]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  // Handle delete
  const handleDelete = async () => {
    if (!deleteModal.page) return;

    setActionLoading(true);
    try {
      await deletePage(deleteModal.page.id);
      setDeleteModal({ open: false, page: null });
      fetchPages();
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error("Error deleting page:", err);
    } finally {
      setActionLoading(false);
    }
  };

  // Handle publish/unpublish toggle
  const handlePublishToggle = async (page) => {
    setActionLoading(true);
    try {
      if (page.is_published) {
        await unpublishPage(page.id);
      } else {
        await publishPage(page.id);
      }
      fetchPages();
    } catch (err) {
      console.error("Error toggling publish state:", err);
    } finally {
      setActionLoading(false);
    }
  };

  // Handle sort
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
    setCurrentPage(1);
  };

  // Reset filters
  const resetFilters = () => {
    setSearchQuery("");
    setCategoryFilter("");
    setLangFilter("");
    setPublishedFilter("");
    setCurrentPage(1);
  };

  // Category options for dropdown
  const categoryOptions = [
    { key: "", value: "", text: "All Categories" },
    ...categories.map((cat) => ({
      key: cat.id,
      value: cat.id,
      text: cat.name,
    })),
  ];

  // Language options
  const languageOptions = [
    { key: "", value: "", text: "All Languages" },
    { key: "en", value: "en", text: "English" },
    { key: "fr", value: "fr", text: "Français" },
    { key: "es", value: "es", text: "Español" },
    { key: "ar", value: "ar", text: "العربية" },
    { key: "ru", value: "ru", text: "Русский" },
    { key: "zh", value: "zh", text: "中文" },
  ];

  // Published filter options
  const publishedOptions = [
    { key: "", value: "", text: "All Status" },
    { key: "published", value: "published", text: "Published Only" },
    { key: "draft", value: "draft", text: "Drafts Only" },
  ];

  // Sort icon
  const getSortIcon = (field) => {
    if (sortField !== field) return null;
    return sortDirection === "asc" ? "sort up" : "sort down";
  };

  return (
    <div className="page-list">
      {/* Toolbar */}
      <Segment className="page-list-toolbar">
        <div className="toolbar-row">
          <div className="toolbar-left">
            <Input
              icon="search"
              iconPosition="left"
              placeholder="Search pages..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              style={{ width: "250px" }}
            />
            <Dropdown
              selection
              options={categoryOptions}
              value={categoryFilter}
              onChange={(e, { value }) => {
                setCategoryFilter(value);
                setCurrentPage(1);
              }}
              placeholder="Category"
              style={{ minWidth: "150px" }}
            />
            <Dropdown
              selection
              options={languageOptions}
              value={langFilter}
              onChange={(e, { value }) => {
                setLangFilter(value);
                setCurrentPage(1);
              }}
              placeholder="Language"
              style={{ minWidth: "120px" }}
            />
            <Dropdown
              selection
              options={publishedOptions}
              value={publishedFilter}
              onChange={(e, { value }) => {
                setPublishedFilter(value);
                setCurrentPage(1);
              }}
              placeholder="Status"
              style={{ minWidth: "130px" }}
            />
            {(searchQuery ||
              categoryFilter ||
              langFilter ||
              publishedFilter) && (
              <Button basic icon onClick={resetFilters} title="Reset filters">
                <Icon name="times" />
              </Button>
            )}
          </div>
          <div className="toolbar-right">
            <Button primary onClick={() => onEdit(null)}>
              <Icon name="plus" />
              New Page
            </Button>
          </div>
        </div>
      </Segment>

      {/* Error message */}
      {error && (
        <Message negative>
          <Message.Header>Error</Message.Header>
          <p>{error}</p>
        </Message>
      )}

      {/* Table */}
      <Segment className="page-list-table">
        <Dimmer active={loading} inverted>
          <Loader>Loading pages...</Loader>
        </Dimmer>

        <Table sortable selectable>
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell
                sorted={
                  sortField === "title"
                    ? sortDirection === "asc"
                      ? "ascending"
                      : "descending"
                    : null
                }
                onClick={() => handleSort("title")}
              >
                Title
                {getSortIcon("title") && <Icon name={getSortIcon("title")} />}
              </Table.HeaderCell>
              <Table.HeaderCell>Slug</Table.HeaderCell>
              <Table.HeaderCell
                sorted={
                  sortField === "lang"
                    ? sortDirection === "asc"
                      ? "ascending"
                      : "descending"
                    : null
                }
                onClick={() => handleSort("lang")}
              >
                Lang
              </Table.HeaderCell>
              <Table.HeaderCell>Status</Table.HeaderCell>
              <Table.HeaderCell
                sorted={
                  sortField === "created"
                    ? sortDirection === "asc"
                      ? "ascending"
                      : "descending"
                    : null
                }
                onClick={() => handleSort("created")}
              >
                Created
              </Table.HeaderCell>
              <Table.HeaderCell
                sorted={
                  sortField === "updated"
                    ? sortDirection === "asc"
                      ? "ascending"
                      : "descending"
                    : null
                }
                onClick={() => handleSort("updated")}
              >
                Updated
              </Table.HeaderCell>
              <Table.HeaderCell textAlign="center">Actions</Table.HeaderCell>
            </Table.Row>
          </Table.Header>

          <Table.Body>
            {pages.length === 0 && !loading ? (
              <Table.Row>
                <Table.Cell colSpan={7} textAlign="center">
                  <Message info>
                    <Icon name="info circle" />
                    No pages found.{" "}
                    {searchQuery && "Try a different search query."}
                  </Message>
                </Table.Cell>
              </Table.Row>
            ) : (
              pages.map((page) => (
                <Table.Row key={page.id}>
                  <Table.Cell>
                    <strong>{page.title}</strong>
                    {page.categories && page.categories.length > 0 && (
                      <div style={{ marginTop: "4px" }}>
                        {page.categories.map((cat) => (
                          <Label key={cat.id} size="tiny" basic>
                            {cat.name}
                          </Label>
                        ))}
                      </div>
                    )}
                  </Table.Cell>
                  <Table.Cell>
                    <code>{page.slug}</code>
                  </Table.Cell>
                  <Table.Cell>
                    <Label size="tiny">
                      {page.lang?.toUpperCase() || "EN"}
                    </Label>
                  </Table.Cell>
                  <Table.Cell>
                    {page.is_published ? (
                      <Label color="green" size="tiny">
                        <Icon name="check" /> Published
                      </Label>
                    ) : (
                      <Label color="grey" size="tiny">
                        <Icon name="pencil" /> Draft
                      </Label>
                    )}
                  </Table.Cell>
                  <Table.Cell>
                    {page.created &&
                      new Date(page.created).toLocaleDateString()}
                  </Table.Cell>
                  <Table.Cell>
                    {page.updated &&
                      new Date(page.updated).toLocaleDateString()}
                  </Table.Cell>
                  <Table.Cell textAlign="center">
                    <Button.Group size="tiny">
                      <Popup
                        content="Edit page"
                        trigger={
                          <Button icon onClick={() => onEdit(page)}>
                            <Icon name="edit" />
                          </Button>
                        }
                      />
                      <Popup
                        content={page.is_published ? "Unpublish" : "Publish"}
                        trigger={
                          <Button
                            icon
                            onClick={() => handlePublishToggle(page)}
                            disabled={actionLoading}
                          >
                            <Icon
                              name={page.is_published ? "eye slash" : "eye"}
                            />
                          </Button>
                        }
                      />
                      <Popup
                        content="Delete page"
                        trigger={
                          <Button
                            icon
                            negative
                            onClick={() => setDeleteModal({ open: true, page })}
                          >
                            <Icon name="trash" />
                          </Button>
                        }
                      />
                    </Button.Group>
                  </Table.Cell>
                </Table.Row>
              ))
            )}
          </Table.Body>

          <Table.Footer>
            <Table.Row>
              <Table.HeaderCell colSpan={7}>
                <div className="table-footer">
                  <span className="total-count">
                    Showing {pages.length} of {totalItems} pages
                  </span>
                  {totalPages > 1 && (
                    <Pagination
                      activePage={currentPage}
                      totalPages={totalPages}
                      onPageChange={(e, { activePage }) =>
                        setCurrentPage(activePage)
                      }
                      size="mini"
                      boundaryRange={1}
                      siblingRange={1}
                      ellipsisItem={{
                        content: <Icon name="ellipsis horizontal" />,
                        icon: true,
                      }}
                      firstItem={{
                        content: <Icon name="angle double left" />,
                        icon: true,
                      }}
                      lastItem={{
                        content: <Icon name="angle double right" />,
                        icon: true,
                      }}
                      prevItem={{
                        content: <Icon name="angle left" />,
                        icon: true,
                      }}
                      nextItem={{
                        content: <Icon name="angle right" />,
                        icon: true,
                      }}
                    />
                  )}
                </div>
              </Table.HeaderCell>
            </Table.Row>
          </Table.Footer>
        </Table>
      </Segment>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        open={deleteModal.open}
        onClose={() => setDeleteModal({ open: false, page: null })}
        onConfirm={handleDelete}
        title="Delete Page"
        message={`Are you sure you want to delete "${deleteModal.page?.title}"? This action cannot be undone.`}
        confirmText="Delete"
        confirmColor="red"
        loading={actionLoading}
      />
    </div>
  );
};

PageList.propTypes = {
  onEdit: PropTypes.func.isRequired,
  onRefresh: PropTypes.func,
};

export default PageList;
