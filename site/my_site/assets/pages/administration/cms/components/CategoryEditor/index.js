// CategoryEditor Component
// Form for creating and editing CMS categories

import React, { useState, useEffect } from "react";
import {
  Form,
  Button,
  Icon,
  Message,
  Segment,
  Divider,
  Checkbox,
} from "semantic-ui-react";
import PropTypes from "prop-types";

import { useCMSApi } from "../../hooks/useCMSApi";

// Initial empty category state
const EMPTY_CATEGORY = {
  name: "",
  slug: "",
  description: "",
  sort_order: 0,
  is_active: true,
};

const CategoryEditor = ({ category, onSave, onCancel }) => {
  const [formData, setFormData] = useState(EMPTY_CATEGORY);
  const [errors, setErrors] = useState({});
  const [isDirty, setIsDirty] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // API hook
  const { loading, createCategory, updateCategory } = useCMSApi();

  // Load category data if editing
  useEffect(() => {
    if (category) {
      setFormData({
        ...EMPTY_CATEGORY,
        ...category,
      });
    } else {
      setFormData(EMPTY_CATEGORY);
    }
    setIsDirty(false);
    setSaveError(null);
    setSaveSuccess(false);
  }, [category]);

  // Handle input change
  const handleChange = (e, { name, value, checked }) => {
    const newValue = checked !== undefined ? checked : value;
    setFormData((prev) => ({ ...prev, [name]: newValue }));
    setIsDirty(true);
    setSaveSuccess(false);

    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  // Auto-generate slug from name
  const generateSlug = () => {
    const slug = formData.name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .trim();
    handleChange(null, { name: "slug", value: slug });
  };

  // Validate form
  const validate = () => {
    const newErrors = {};

    if (!formData.name?.trim()) {
      newErrors.name = "Name is required";
    }

    if (!formData.slug?.trim()) {
      newErrors.slug = "Slug is required";
    } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      newErrors.slug =
        "Slug can only contain lowercase letters, numbers, and hyphens";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle save
  const handleSave = async () => {
    if (!validate()) return;

    setSaveError(null);
    setSaveSuccess(false);

    // Extract only editable fields (exclude read-only fields like id, created, updated, links)
    const payload = {
      name: formData.name,
      slug: formData.slug,
      description: formData.description,
      sort_order: formData.sort_order,
      is_active: formData.is_active,
    };

    try {
      let savedCategory;
      if (category?.id) {
        savedCategory = await updateCategory(category.id, payload);
      } else {
        savedCategory = await createCategory(payload);
      }

      setIsDirty(false);
      setSaveSuccess(true);

      if (onSave) {
        onSave(savedCategory);
      }
    } catch (err) {
      setSaveError(err.message || "Error saving category");
    }
  };

  return (
    <div className="category-editor">
      <Segment>
        <div className="editor-header">
          <h2>
            <Icon name={category?.id ? "edit" : "plus"} />
            {category?.id ? "Edit Category" : "New Category"}
          </h2>
          <div className="editor-actions">
            <Button basic onClick={onCancel} disabled={loading}>
              <Icon name="arrow left" />
              Back to List
            </Button>
          </div>
        </div>

        <Divider />

        {saveError && (
          <Message negative>
            <Message.Header>Error</Message.Header>
            <p>{saveError}</p>
          </Message>
        )}

        {saveSuccess && (
          <Message positive>
            <Message.Header>Success</Message.Header>
            <p>Category saved successfully!</p>
          </Message>
        )}

        <Form loading={loading}>
          <Form.Input
            label="Name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Category name"
            required
            error={
              errors.name ? { content: errors.name, pointing: "below" } : null
            }
          />

          <Form.Field required error={!!errors.slug}>
            {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
            <label>
              Slug
              <Button
                type="button"
                size="tiny"
                basic
                onClick={generateSlug}
                style={{ marginLeft: "10px" }}
                disabled={!formData.name}
              >
                <Icon name="magic" /> Generate from name
              </Button>
            </label>
            <Form.Input
              name="slug"
              value={formData.slug}
              onChange={handleChange}
              placeholder="category-slug"
              error={errors.slug ? { content: errors.slug } : null}
            />
          </Form.Field>

          <Form.TextArea
            label="Description"
            name="description"
            value={formData.description || ""}
            onChange={handleChange}
            placeholder="Category description"
            rows={3}
          />

          <Form.Input
            label="Sort Order"
            type="number"
            name="sort_order"
            value={formData.sort_order}
            onChange={handleChange}
            min={0}
            style={{ width: "120px" }}
          />
          <small
            style={{
              color: "#888",
              marginTop: "-1em",
              display: "block",
              marginBottom: "1em",
            }}
          >
            Lower numbers appear first
          </small>

          <Form.Field>
            <Checkbox
              name="is_active"
              label="Active"
              checked={formData.is_active}
              onChange={handleChange}
            />
          </Form.Field>

          <Divider />

          <div className="editor-footer">
            <Button primary onClick={handleSave} disabled={loading || !isDirty}>
              <Icon name="save" />
              Save Category
            </Button>

            {isDirty && (
              <span style={{ marginLeft: "1rem", color: "#f2711c" }}>
                <Icon name="warning" /> Unsaved changes
              </span>
            )}
          </div>
        </Form>
      </Segment>
    </div>
  );
};

CategoryEditor.propTypes = {
  category: PropTypes.object,
  onSave: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};

export default CategoryEditor;
