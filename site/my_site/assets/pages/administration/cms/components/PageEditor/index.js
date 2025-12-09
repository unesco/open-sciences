// PageEditor Component
// Form for creating and editing CMS pages

import React, { useState, useEffect, useCallback } from "react";
import {
  Form,
  Button,
  Icon,
  Message,
  Segment,
  Grid,
  Divider,
  Tab,
  Label,
  Dropdown,
  TextArea,
} from "semantic-ui-react";
import PropTypes from "prop-types";

import { useCMSApi } from "../../hooks/useCMSApi";

// Initial empty page state
const EMPTY_PAGE = {
  title: "",
  slug: "",
  content: "",
  excerpt: "",
  meta_title: "",
  meta_description: "",
  meta_keywords: "",
  template_name: "default",
  lang: "en",
  sort_order: 0,
  is_published: false,
  category_ids: [],
};

const PageEditor = ({ page, onSave, onCancel }) => {
  const [formData, setFormData] = useState(EMPTY_PAGE);
  const [categories, setCategories] = useState([]);
  const [errors, setErrors] = useState({});
  const [isDirty, setIsDirty] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // API hook
  const { loading, createPage, updatePage, listCategories } = useCMSApi();

  // Load page data if editing
  useEffect(() => {
    if (page) {
      setFormData({
        ...EMPTY_PAGE,
        ...page,
        category_ids: page.categories?.map((c) => c.id) || [],
      });
    } else {
      setFormData(EMPTY_PAGE);
    }
    setIsDirty(false);
    setSaveError(null);
    setSaveSuccess(false);
  }, [page]);

  // Fetch categories
  const fetchCategories = useCallback(async () => {
    try {
      const result = await listCategories({ size: 100, active_only: true });
      setCategories(result.hits || []);
    } catch (err) {
      console.error("Error fetching categories:", err);
    }
  }, [listCategories]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  // Handle input change
  const handleChange = (e, { name, value }) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
    setIsDirty(true);
    setSaveSuccess(false);

    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  // Auto-generate slug from title
  const generateSlug = () => {
    const slug = formData.title
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

    if (!formData.title?.trim()) {
      newErrors.title = "Title is required";
    }

    if (!formData.slug?.trim()) {
      newErrors.slug = "Slug is required";
    } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      newErrors.slug =
        "Slug can only contain lowercase letters, numbers, and hyphens";
    }

    if (!formData.content?.trim()) {
      newErrors.content = "Content is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle save
  const handleSave = async (publish = false) => {
    if (!validate()) return;

    setSaveError(null);
    setSaveSuccess(false);

    try {
      // Extract only editable fields (exclude read-only fields like id, created, updated, author, categories, links)
      const payload = {
        slug: formData.slug,
        title: formData.title,
        content: formData.content,
        excerpt: formData.excerpt,
        meta_title: formData.meta_title,
        meta_description: formData.meta_description,
        template_name: formData.template_name,
        is_published: publish ? true : formData.is_published,
        lang: formData.lang,
        sort_order: formData.sort_order,
        category_ids: formData.category_ids,
      };

      let savedPage;
      if (page?.id) {
        savedPage = await updatePage(page.id, payload);
      } else {
        savedPage = await createPage(payload);
      }

      setIsDirty(false);
      setSaveSuccess(true);

      if (onSave) {
        onSave(savedPage);
      }
    } catch (err) {
      setSaveError(err.message || "Error saving page");
    }
  };

  // Category options
  const categoryOptions = categories.map((cat) => ({
    key: cat.id,
    value: cat.id,
    text: cat.name,
  }));

  // Language options
  const languageOptions = [
    { key: "en", value: "en", text: "English" },
    { key: "fr", value: "fr", text: "Français" },
    { key: "es", value: "es", text: "Español" },
    { key: "ar", value: "ar", text: "العربية" },
    { key: "ru", value: "ru", text: "Русский" },
    { key: "zh", value: "zh", text: "中文" },
  ];

  // Template options
  const templateOptions = [
    { key: "default", value: "default", text: "Default" },
    { key: "full-width", value: "full-width", text: "Full Width" },
    { key: "sidebar-left", value: "sidebar-left", text: "Sidebar Left" },
    { key: "sidebar-right", value: "sidebar-right", text: "Sidebar Right" },
    { key: "landing", value: "landing", text: "Landing Page" },
  ];

  // Tab panes
  const panes = [
    {
      menuItem: { key: "content", icon: "file text", content: "Content" },
      render: () => (
        <Tab.Pane>
          <Form.Input
            label="Title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Page title"
            required
            error={
              errors.title ? { content: errors.title, pointing: "below" } : null
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
                disabled={!formData.title}
              >
                <Icon name="magic" /> Generate from title
              </Button>
            </label>
            <Form.Input
              name="slug"
              value={formData.slug}
              onChange={handleChange}
              placeholder="page-url-slug"
              error={errors.slug ? { content: errors.slug } : null}
            />
          </Form.Field>

          <Form.TextArea
            label="Excerpt"
            name="excerpt"
            value={formData.excerpt || ""}
            onChange={handleChange}
            placeholder="Brief description of the page"
            rows={3}
          />

          <Form.Field required error={!!errors.content}>
            {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
            <label>Content (HTML)</label>
            <TextArea
              name="content"
              value={formData.content || ""}
              onChange={handleChange}
              placeholder="Page content in HTML format"
              rows={15}
              style={{ fontFamily: "monospace" }}
            />
            {errors.content && (
              <Label basic color="red" pointing>
                {errors.content}
              </Label>
            )}
          </Form.Field>
        </Tab.Pane>
      ),
    },
    {
      menuItem: { key: "settings", icon: "cog", content: "Settings" },
      render: () => (
        <Tab.Pane>
          <Grid columns={2} stackable>
            <Grid.Column>
              <Form.Field>
                {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                <label>Language</label>
                <Dropdown
                  selection
                  name="lang"
                  options={languageOptions}
                  value={formData.lang}
                  onChange={handleChange}
                />
              </Form.Field>

              <Form.Field>
                {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                <label>Template</label>
                <Dropdown
                  selection
                  name="template_name"
                  options={templateOptions}
                  value={formData.template_name}
                  onChange={handleChange}
                />
              </Form.Field>

              <Form.Input
                label="Sort Order"
                type="number"
                name="sort_order"
                value={formData.sort_order}
                onChange={handleChange}
                min={0}
              />
            </Grid.Column>

            <Grid.Column>
              <Form.Field>
                {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                <label>Categories</label>
                <Dropdown
                  multiple
                  selection
                  name="category_ids"
                  options={categoryOptions}
                  value={formData.category_ids}
                  onChange={handleChange}
                  placeholder="Select categories"
                />
              </Form.Field>

              <Form.Field>
                {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                <label>Status</label>
                <div>
                  {formData.is_published ? (
                    <Label color="green">
                      <Icon name="check" /> Published
                    </Label>
                  ) : (
                    <Label color="grey">
                      <Icon name="pencil" /> Draft
                    </Label>
                  )}
                </div>
              </Form.Field>

              {page?.published_at && (
                <Form.Field>
                  {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                  <label>Published Date</label>
                  <span>{new Date(page.published_at).toLocaleString()}</span>
                </Form.Field>
              )}
            </Grid.Column>
          </Grid>
        </Tab.Pane>
      ),
    },
    {
      menuItem: { key: "seo", icon: "search", content: "SEO" },
      render: () => (
        <Tab.Pane>
          <Form.Input
            label="Meta Title"
            name="meta_title"
            value={formData.meta_title || ""}
            onChange={handleChange}
            placeholder="SEO title (leave empty to use page title)"
            maxLength={70}
          />
          <small
            style={{
              color: "#888",
              marginTop: "-1em",
              display: "block",
              marginBottom: "1em",
            }}
          >
            {formData.meta_title?.length || 0}/70 characters
          </small>

          <Form.TextArea
            label="Meta Description"
            name="meta_description"
            value={formData.meta_description || ""}
            onChange={handleChange}
            placeholder="SEO description"
            rows={3}
            maxLength={160}
          />
          <small
            style={{
              color: "#888",
              marginTop: "-1em",
              display: "block",
              marginBottom: "1em",
            }}
          >
            {formData.meta_description?.length || 0}/160 characters
          </small>

          <Form.Input
            label="Meta Keywords"
            name="meta_keywords"
            value={formData.meta_keywords || ""}
            onChange={handleChange}
            placeholder="keyword1, keyword2, keyword3"
          />
          <small
            style={{
              color: "#888",
              marginTop: "-1em",
              display: "block",
              marginBottom: "1em",
            }}
          >
            Comma-separated list of keywords
          </small>
        </Tab.Pane>
      ),
    },
  ];

  return (
    <div className="page-editor">
      <Segment>
        <div className="editor-header">
          <h2>
            <Icon name={page?.id ? "edit" : "plus"} />
            {page?.id ? "Edit Page" : "New Page"}
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
            <p>Page saved successfully!</p>
          </Message>
        )}

        <Form loading={loading}>
          <Tab panes={panes} />

          <Divider />

          <div className="editor-footer">
            <Button.Group>
              <Button
                primary
                onClick={() => handleSave(false)}
                disabled={loading || !isDirty}
              >
                <Icon name="save" />
                Save Draft
              </Button>
              <Button.Or />
              <Button
                positive
                onClick={() => handleSave(true)}
                disabled={loading}
              >
                <Icon name="send" />
                Save & Publish
              </Button>
            </Button.Group>

            {isDirty && (
              <Label basic color="orange" style={{ marginLeft: "1rem" }}>
                <Icon name="warning" /> Unsaved changes
              </Label>
            )}
          </div>
        </Form>
      </Segment>
    </div>
  );
};

PageEditor.propTypes = {
  page: PropTypes.object,
  onSave: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};

export default PageEditor;
