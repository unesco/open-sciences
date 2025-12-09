// CategoryList Component
// Displays a list of CMS categories with CRUD operations

import React, { useState, useEffect, useCallback } from "react";
import {
  Table,
  Button,
  Input,
  Icon,
  Label,
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

const CategoryList = ({ onEdit, onRefresh }) => {
  // State
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");

  // Modal state
  const [deleteModal, setDeleteModal] = useState({
    open: false,
    category: null,
  });
  const [actionLoading, setActionLoading] = useState(false);

  // Debounced search
  const debouncedSearch = useDebounce(searchQuery, 300);

  // API hook
  const { loading, error, listCategories, deleteCategory } = useCMSApi();

  // Fetch categories
  const fetchCategories = useCallback(async () => {
    try {
      const params = { size: 100 };
      if (debouncedSearch) params.q = debouncedSearch;

      const result = await listCategories(params);
      setCategories(result.hits || []);
    } catch (err) {
      console.error("Error fetching categories:", err);
    }
  }, [debouncedSearch, listCategories]);

  // Initial load
  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  // Handle delete
  const handleDelete = async () => {
    if (!deleteModal.category) return;

    setActionLoading(true);
    try {
      await deleteCategory(deleteModal.category.id);
      setDeleteModal({ open: false, category: null });
      fetchCategories();
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error("Error deleting category:", err);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="category-list">
      {/* Toolbar */}
      <Segment className="category-list-toolbar">
        <div className="toolbar-row">
          <div className="toolbar-left">
            <Input
              icon="search"
              iconPosition="left"
              placeholder="Search categories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ width: "250px" }}
            />
            {searchQuery && (
              <Button
                basic
                icon
                onClick={() => setSearchQuery("")}
                title="Clear search"
              >
                <Icon name="times" />
              </Button>
            )}
          </div>
          <div className="toolbar-right">
            <Button primary onClick={() => onEdit(null)}>
              <Icon name="plus" />
              New Category
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
      <Segment className="category-list-table">
        <Dimmer active={loading} inverted>
          <Loader>Loading categories...</Loader>
        </Dimmer>

        <Table selectable>
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell>Name</Table.HeaderCell>
              <Table.HeaderCell>Slug</Table.HeaderCell>
              <Table.HeaderCell>Description</Table.HeaderCell>
              <Table.HeaderCell textAlign="center">Sort Order</Table.HeaderCell>
              <Table.HeaderCell textAlign="center">Status</Table.HeaderCell>
              <Table.HeaderCell>Created</Table.HeaderCell>
              <Table.HeaderCell textAlign="center">Actions</Table.HeaderCell>
            </Table.Row>
          </Table.Header>

          <Table.Body>
            {categories.length === 0 && !loading ? (
              <Table.Row>
                <Table.Cell colSpan={7} textAlign="center">
                  <Message info>
                    <Icon name="info circle" />
                    No categories found.{" "}
                    {searchQuery && "Try a different search query."}
                  </Message>
                </Table.Cell>
              </Table.Row>
            ) : (
              categories.map((category) => (
                <Table.Row key={category.id}>
                  <Table.Cell>
                    <strong>{category.name}</strong>
                  </Table.Cell>
                  <Table.Cell>
                    <code>{category.slug}</code>
                  </Table.Cell>
                  <Table.Cell>
                    {category.description
                      ? category.description.length > 50
                        ? `${category.description.substring(0, 50)}...`
                        : category.description
                      : "-"}
                  </Table.Cell>
                  <Table.Cell textAlign="center">
                    {category.sort_order}
                  </Table.Cell>
                  <Table.Cell textAlign="center">
                    {category.is_active ? (
                      <Label color="green" size="tiny">
                        <Icon name="check" /> Active
                      </Label>
                    ) : (
                      <Label color="grey" size="tiny">
                        <Icon name="pause" /> Inactive
                      </Label>
                    )}
                  </Table.Cell>
                  <Table.Cell>
                    {category.created &&
                      new Date(category.created).toLocaleDateString()}
                  </Table.Cell>
                  <Table.Cell textAlign="center">
                    <Button.Group size="tiny">
                      <Popup
                        content="Edit category"
                        trigger={
                          <Button icon onClick={() => onEdit(category)}>
                            <Icon name="edit" />
                          </Button>
                        }
                      />
                      <Popup
                        content="Delete category"
                        trigger={
                          <Button
                            icon
                            negative
                            onClick={() =>
                              setDeleteModal({ open: true, category })
                            }
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
        </Table>
      </Segment>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        open={deleteModal.open}
        onClose={() => setDeleteModal({ open: false, category: null })}
        onConfirm={handleDelete}
        title="Delete Category"
        message={`Are you sure you want to delete "${deleteModal.category?.name}"? Pages associated with this category will be unlinked.`}
        confirmText="Delete"
        confirmColor="red"
        loading={actionLoading}
      />
    </div>
  );
};

CategoryList.propTypes = {
  onEdit: PropTypes.func.isRequired,
  onRefresh: PropTypes.func,
};

export default CategoryList;
