/**
 * ContentEditor Component
 * Dynamic form editor based on JSON Schema for CMS content
 */

import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import {
  Form,
  Button,
  Message,
  Header,
  Segment,
  Icon,
  Divider,
  Label,
} from "semantic-ui-react";
import { useResourceCMSApi } from "../../hooks";

/**
 * DynamicField - Renders a form field based on JSON Schema property
 */
const DynamicField = ({ name, schema, value, onChange, required }) => {
  const handleChange = (e, { value: newValue }) => {
    onChange(name, newValue);
  };

  const handleArrayChange = (index, newValue) => {
    const arr = [...(value || [])];
    arr[index] = newValue;
    onChange(name, arr);
  };

  const handleAddArrayItem = () => {
    const arr = [...(value || [])];
    // Determine default value based on items type
    const itemType = schema.items?.type || "string";
    const defaultValue =
      itemType === "object" ? {} : itemType === "number" ? 0 : "";
    arr.push(defaultValue);
    onChange(name, arr);
  };

  const handleRemoveArrayItem = (index) => {
    const arr = [...(value || [])];
    arr.splice(index, 1);
    onChange(name, arr);
  };

  const handleObjectChange = (propName, newValue) => {
    const obj = { ...(value || {}) };
    obj[propName] = newValue;
    onChange(name, obj);
  };

  // Get label from schema or format name
  const label =
    schema.title ||
    name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  // Handle different types
  switch (schema.type) {
    case "string":
      if (schema.enum) {
        // Dropdown for enum
        return (
          <Form.Select
            label={label}
            options={schema.enum.map((opt) => ({
              key: opt,
              text: opt,
              value: opt,
            }))}
            value={value || ""}
            onChange={handleChange}
            required={required}
          />
        );
      }
      if (schema.format === "textarea" || schema.maxLength > 255) {
        // Textarea for long strings
        return (
          <Form.TextArea
            label={label}
            value={value || ""}
            onChange={handleChange}
            required={required}
            rows={4}
          />
        );
      }
      if (schema.format === "html") {
        // HTML editor (simple textarea for now, could be replaced with rich editor)
        return (
          <Form.Field required={required}>
            <label>{label}</label>
            <textarea
              value={value || ""}
              onChange={(e) => onChange(name, e.target.value)}
              rows={8}
              style={{ fontFamily: "monospace" }}
            />
            <small style={{ color: "#888" }}>HTML content allowed</small>
          </Form.Field>
        );
      }
      // Default text input
      return (
        <Form.Input
          label={label}
          value={value || ""}
          onChange={handleChange}
          required={required}
          type={schema.format === "email" ? "email" : "text"}
        />
      );

    case "number":
    case "integer":
      return (
        <Form.Input
          label={label}
          type="number"
          value={value ?? ""}
          onChange={(e, { value: v }) =>
            onChange(name, v === "" ? null : Number(v))
          }
          required={required}
          min={schema.minimum}
          max={schema.maximum}
        />
      );

    case "boolean":
      return (
        <Form.Checkbox
          label={label}
          checked={!!value}
          onChange={(e, { checked }) => onChange(name, checked)}
        />
      );

    case "array":
      return (
        <Form.Field required={required}>
          <label>{label}</label>
          <Segment>
            {(value || []).map((item, index) => (
              <div
                key={index}
                style={{
                  marginBottom: "0.5em",
                  display: "flex",
                  alignItems: "center",
                }}
              >
                {schema.items?.type === "object" ? (
                  // Nested object in array
                  <Segment style={{ flex: 1, marginBottom: 0 }}>
                    {Object.entries(schema.items.properties || {}).map(
                      ([propName, propSchema]) => (
                        <DynamicField
                          key={propName}
                          name={propName}
                          schema={propSchema}
                          value={item?.[propName]}
                          onChange={(n, v) => {
                            const newItem = { ...item, [n]: v };
                            handleArrayChange(index, newItem);
                          }}
                          required={schema.items.required?.includes(propName)}
                        />
                      )
                    )}
                  </Segment>
                ) : (
                  // Simple value in array
                  <Form.Input
                    value={item || ""}
                    onChange={(e, { value: v }) => handleArrayChange(index, v)}
                    style={{ flex: 1 }}
                  />
                )}
                <Button
                  icon="trash"
                  basic
                  negative
                  size="small"
                  onClick={() => handleRemoveArrayItem(index)}
                  style={{ marginLeft: "0.5em" }}
                />
              </div>
            ))}
            <Button
              icon="plus"
              basic
              size="small"
              content="Add Item"
              onClick={handleAddArrayItem}
            />
          </Segment>
        </Form.Field>
      );

    case "object":
      return (
        <Form.Field required={required}>
          <label>{label}</label>
          <Segment>
            {Object.entries(schema.properties || {}).map(
              ([propName, propSchema]) => (
                <DynamicField
                  key={propName}
                  name={propName}
                  schema={propSchema}
                  value={value?.[propName]}
                  onChange={(n, v) => handleObjectChange(n, v)}
                  required={schema.required?.includes(propName)}
                />
              )
            )}
          </Segment>
        </Form.Field>
      );

    default:
      return (
        <Form.Input
          label={label}
          value={value || ""}
          onChange={handleChange}
          required={required}
        />
      );
  }
};

DynamicField.propTypes = {
  name: PropTypes.string.isRequired,
  schema: PropTypes.object.isRequired,
  value: PropTypes.any,
  onChange: PropTypes.func.isRequired,
  required: PropTypes.bool,
};

/**
 * ContentEditor - Main editor component
 */
export const ContentEditor = ({
  resourceType,
  resourceDefinition,
  content,
  onSave,
  onCancel,
}) => {
  const { createContent, updateContent, loading, error, setError } =
    useResourceCMSApi();

  const isNew = !content?.id;
  const isSingleton = resourceDefinition?.is_singleton;

  // Form state
  const [formData, setFormData] = useState({
    slug: "",
    lang: "en",
    data: {},
  });
  const [validationErrors, setValidationErrors] = useState([]);

  // Initialize form with content data
  useEffect(() => {
    if (content) {
      setFormData({
        slug: content.slug || "",
        lang: content.lang || "en",
        data: content.data || {},
      });
    } else if (isSingleton) {
      setFormData({
        slug: resourceType,
        lang: "en",
        data: {},
      });
    }
  }, [content, isSingleton, resourceType]);

  // Handle data field changes
  const handleDataChange = (name, value) => {
    setFormData((prev) => ({
      ...prev,
      data: {
        ...prev.data,
        [name]: value,
      },
    }));
  };

  // Handle metadata field changes
  const handleFieldChange = (e, { name, value }) => {
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Handle form submission
  const handleSubmit = async () => {
    setValidationErrors([]);
    setError(null);

    try {
      let result;
      if (isNew) {
        result = await createContent(resourceType, formData);
      } else {
        result = await updateContent(resourceType, content.id, formData);
      }
      onSave(result);
    } catch (err) {
      console.error("Error saving content:", err);
      if (err.message.includes("validation")) {
        setValidationErrors([err.message]);
      }
    }
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

  // Get schema for data field
  const schema = resourceDefinition?.schema || {
    type: "object",
    properties: {},
  };
  const dataProperties = schema.properties || {};
  const requiredFields = schema.required || [];

  return (
    <div className="content-editor">
      {/* Header Card */}
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
                {isNew ? "Create New" : "Edit"}{" "}
                {resourceDefinition?.label || resourceType}
              </Header>
              <p style={{ margin: 0, opacity: 0.85, fontSize: "0.95rem" }}>
                {resourceDefinition?.description ||
                  "Configure content settings and data"}
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
            <Icon name={isSingleton ? "cube" : "copy"} />
            {isSingleton ? "Singleton" : "Collection"}
          </Label>
        </div>
      </Segment>

      {error && (
        <Message negative icon>
          <Icon name="warning circle" />
          <Message.Content>
            <Message.Header>Error saving content</Message.Header>
            <p>{error}</p>
          </Message.Content>
        </Message>
      )}

      {validationErrors.length > 0 && (
        <Message negative icon>
          <Icon name="exclamation triangle" />
          <Message.Content>
            <Message.Header>Validation Errors</Message.Header>
            <ul style={{ margin: "0.5rem 0 0 0", paddingLeft: "1.5rem" }}>
              {validationErrors.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          </Message.Content>
        </Message>
      )}

      <Form loading={loading} onSubmit={handleSubmit}>
        {/* Metadata Section */}
        <Segment raised style={{ borderRadius: "8px" }}>
          <Header as="h4" style={{ color: "#555", marginBottom: "1rem" }}>
            <Icon name="cog" color="grey" />
            <Header.Content>
              Settings
              <Header.Subheader>Basic content configuration</Header.Subheader>
            </Header.Content>
          </Header>

          <Form.Group widths="equal">
            <Form.Field required disabled={isSingleton}>
              <span
                style={{
                  fontWeight: "bold",
                  display: "block",
                  marginBottom: "0.5rem",
                }}
              >
                <Icon name="linkify" /> URL Slug
              </span>
              <input
                name="slug"
                value={formData.slug}
                onChange={handleFieldChange}
                placeholder="my-content-slug"
                style={{
                  opacity: isSingleton ? 0.6 : 1,
                  width: "100%",
                  padding: "0.67857143em 1em",
                  border: "1px solid rgba(34,36,38,.15)",
                  borderRadius: ".28571429rem",
                }}
                disabled={isSingleton}
              />
            </Form.Field>
            <Form.Field>
              <span
                style={{
                  fontWeight: "bold",
                  display: "block",
                  marginBottom: "0.5rem",
                }}
              >
                <Icon name="globe" /> Language
              </span>
              <Form.Select
                name="lang"
                value={formData.lang}
                onChange={handleFieldChange}
                options={[
                  { key: "en", text: "🇬🇧 English", value: "en" },
                  { key: "fr", text: "🇫🇷 Français", value: "fr" },
                  { key: "es", text: "🇪🇸 Español", value: "es" },
                  { key: "ar", text: "🇸🇦 العربية", value: "ar" },
                  { key: "zh", text: "🇨🇳 中文", value: "zh" },
                  { key: "ru", text: "🇷🇺 Русский", value: "ru" },
                ]}
                style={{ minWidth: "100%" }}
              />
            </Form.Field>
          </Form.Group>
        </Segment>

        {/* Content Data Section */}
        <Segment raised style={{ borderRadius: "8px", marginTop: "1.5rem" }}>
          <Header as="h4" style={{ color: "#555", marginBottom: "1rem" }}>
            <Icon name="edit outline" color="blue" />
            <Header.Content>
              Content
              <Header.Subheader>Edit the content fields below</Header.Subheader>
            </Header.Content>
          </Header>

          {Object.keys(dataProperties).length === 0 ? (
            <Message info icon>
              <Icon name="info circle" />
              <Message.Content>
                <Message.Header>Free-form JSON</Message.Header>
                <p>
                  This resource type has no defined schema. Enter JSON data
                  directly.
                </p>
              </Message.Content>
            </Message>
          ) : null}

          {Object.keys(dataProperties).length === 0 ? (
            <Form.TextArea
              label="JSON Data"
              value={JSON.stringify(formData.data, null, 2)}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value);
                  setFormData((prev) => ({ ...prev, data: parsed }));
                } catch {
                  // Invalid JSON
                }
              }}
              rows={10}
              style={{ fontFamily: "monospace", fontSize: "0.9rem" }}
            />
          ) : (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
              }}
            >
              {Object.entries(dataProperties).map(([propName, propSchema]) => (
                <DynamicField
                  key={propName}
                  name={propName}
                  schema={propSchema}
                  value={formData.data[propName]}
                  onChange={handleDataChange}
                  required={requiredFields.includes(propName)}
                />
              ))}
            </div>
          )}
        </Segment>

        {/* Action Buttons */}
        <div
          style={{
            marginTop: "2rem",
            paddingTop: "1.5rem",
            borderTop: "1px solid #e0e0e0",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Button
            type="button"
            onClick={onCancel}
            size="large"
            basic
            style={{ paddingLeft: "1.5rem", paddingRight: "1.5rem" }}
          >
            <Icon name="arrow left" />
            Back
          </Button>
          <Button
            type="submit"
            primary
            size="large"
            style={{
              paddingLeft: "2rem",
              paddingRight: "2rem",
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            }}
          >
            <Icon name="save" />
            {isNew ? "Create Content" : "Save Changes"}
          </Button>
        </div>
      </Form>
    </div>
  );
};

ContentEditor.propTypes = {
  resourceType: PropTypes.string.isRequired,
  resourceDefinition: PropTypes.object,
  content: PropTypes.object,
  onSave: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};

ContentEditor.defaultProps = {
  resourceDefinition: null,
  content: null,
};

export default ContentEditor;
