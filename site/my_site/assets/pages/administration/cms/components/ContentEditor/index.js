/**
 * ContentEditor Component
 * Dynamic form editor based on JSON Schema for CMS content
 */

import React, { useState, useEffect, useRef } from "react";
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
  Menu,
} from "semantic-ui-react";
import { useResourceCMSApi } from "../../hooks";

/**
 * HtmlEditor - WYSIWYG editor with HTML source code toggle
 *
 * Uses contentEditable with careful state management to avoid cursor jumping issues.
 * The key insight is to NOT re-render the contentEditable div from React state
 * during active editing - only sync when switching modes or on initial load.
 */
const HtmlEditor = ({ label, value, onChange, required, description }) => {
  const [mode, setMode] = useState("visual"); // "visual" or "source"
  const [sourceContent, setSourceContent] = useState(value || "");
  const editorRef = useRef(null);
  const lastExternalValue = useRef(value || "");
  const isUserEditing = useRef(false);

  // Sync from props when value changes externally (e.g., data loaded from API)
  // Only update if the value actually changed AND user is not actively editing
  useEffect(() => {
    if (value !== lastExternalValue.current && !isUserEditing.current) {
      lastExternalValue.current = value || "";
      setSourceContent(value || "");
      if (editorRef.current && mode === "visual") {
        editorRef.current.innerHTML = value || "";
      }
    }
  }, [value, mode]);

  // Sync content when switching modes
  const switchToVisual = () => {
    if (editorRef.current) {
      editorRef.current.innerHTML = sourceContent;
    }
    setMode("visual");
  };

  const switchToSource = () => {
    if (editorRef.current) {
      setSourceContent(editorRef.current.innerHTML);
    }
    setMode("source");
  };

  // Handle focus - mark as editing
  const handleFocus = () => {
    isUserEditing.current = true;
  };

  // Handle visual editor blur - sync to parent
  const handleVisualBlur = () => {
    isUserEditing.current = false;
    if (editorRef.current) {
      const content = editorRef.current.innerHTML;
      setSourceContent(content);
      lastExternalValue.current = content;
      onChange(content);
    }
  };

  // Handle source code changes
  const handleSourceChange = (e) => {
    isUserEditing.current = true;
    const content = e.target.value;
    setSourceContent(content);
    onChange(content);
  };

  // Handle source code blur
  const handleSourceBlur = () => {
    isUserEditing.current = false;
    lastExternalValue.current = sourceContent;
  };

  // Execute formatting command (doesn't trigger re-render)
  const execCommand = (command, commandValue = null) => {
    document.execCommand(command, false, commandValue);
    editorRef.current?.focus();
  };

  // Insert link
  const insertLink = () => {
    const url = prompt("Enter URL:");
    if (url) {
      execCommand("createLink", url);
    }
  };

  // Insert image
  const insertImage = () => {
    const url = prompt("Enter image URL:");
    if (url) {
      execCommand("insertImage", url);
    }
  };

  return (
    <Form.Field required={required}>
      <label>{label}</label>

      {/* Mode toggle and toolbar */}
      <div style={{ marginBottom: "0.5em" }}>
        <Menu secondary size="small" style={{ marginBottom: "0.5em" }}>
          <Menu.Item
            name="visual"
            active={mode === "visual"}
            onClick={switchToVisual}
          >
            <Icon name="eye" /> Visual
          </Menu.Item>
          <Menu.Item
            name="source"
            active={mode === "source"}
            onClick={switchToSource}
          >
            <Icon name="code" /> HTML Source
          </Menu.Item>
        </Menu>

        {/* Formatting toolbar (only in visual mode) */}
        {mode === "visual" && (
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "4px",
              padding: "8px",
              background: "#f9f9f9",
              border: "1px solid #ddd",
              borderBottom: "none",
              borderRadius: "4px 4px 0 0",
            }}
          >
            <Button.Group size="mini" basic>
              <Button
                type="button"
                icon="bold"
                title="Bold"
                onClick={() => execCommand("bold")}
              />
              <Button
                type="button"
                icon="italic"
                title="Italic"
                onClick={() => execCommand("italic")}
              />
              <Button
                type="button"
                icon="underline"
                title="Underline"
                onClick={() => execCommand("underline")}
              />
              <Button
                type="button"
                icon="strikethrough"
                title="Strikethrough"
                onClick={() => execCommand("strikeThrough")}
              />
            </Button.Group>

            <Button.Group size="mini" basic>
              <Button
                type="button"
                icon="list ul"
                title="Bullet List"
                onClick={() => execCommand("insertUnorderedList")}
              />
              <Button
                type="button"
                icon="list ol"
                title="Numbered List"
                onClick={() => execCommand("insertOrderedList")}
              />
            </Button.Group>

            <Button.Group size="mini" basic>
              <Button
                type="button"
                icon="align left"
                title="Align Left"
                onClick={() => execCommand("justifyLeft")}
              />
              <Button
                type="button"
                icon="align center"
                title="Align Center"
                onClick={() => execCommand("justifyCenter")}
              />
              <Button
                type="button"
                icon="align right"
                title="Align Right"
                onClick={() => execCommand("justifyRight")}
              />
            </Button.Group>

            <Button.Group size="mini" basic>
              <Button
                type="button"
                icon="linkify"
                title="Insert Link"
                onClick={insertLink}
              />
              <Button
                type="button"
                icon="unlinkify"
                title="Remove Link"
                onClick={() => execCommand("unlink")}
              />
              <Button
                type="button"
                icon="image"
                title="Insert Image"
                onClick={insertImage}
              />
            </Button.Group>

            <Button.Group size="mini" basic>
              <Button
                type="button"
                icon="indent"
                title="Indent"
                onClick={() => execCommand("indent")}
              />
              <Button
                type="button"
                icon="outdent"
                title="Outdent"
                onClick={() => execCommand("outdent")}
              />
            </Button.Group>

            <Button
              type="button"
              size="mini"
              basic
              icon="eraser"
              title="Clear Formatting"
              onClick={() => execCommand("removeFormat")}
            />

            <select
              onChange={(e) => execCommand("formatBlock", e.target.value)}
              style={{ marginLeft: "8px", padding: "4px", fontSize: "12px" }}
              defaultValue=""
            >
              <option value="" disabled>
                Format
              </option>
              <option value="p">Paragraph</option>
              <option value="h1">Heading 1</option>
              <option value="h2">Heading 2</option>
              <option value="h3">Heading 3</option>
              <option value="h4">Heading 4</option>
              <option value="blockquote">Quote</option>
              <option value="pre">Code</option>
            </select>
          </div>
        )}
      </div>

      {/* Editor content */}
      {mode === "visual" ? (
        <div
          ref={editorRef}
          contentEditable
          onFocus={handleFocus}
          onBlur={handleVisualBlur}
          style={{
            minHeight: "300px",
            maxHeight: "600px",
            overflowY: "auto",
            padding: "16px",
            border: "1px solid #ddd",
            borderRadius: "0 0 4px 4px",
            background: "#fff",
            outline: "none",
          }}
        />
      ) : (
        <textarea
          value={sourceContent}
          onChange={handleSourceChange}
          onBlur={handleSourceBlur}
          rows={15}
          style={{
            width: "100%",
            fontFamily: "Monaco, Consolas, 'Courier New', monospace",
            fontSize: "13px",
            lineHeight: "1.5",
            padding: "16px",
            border: "1px solid #ddd",
            borderRadius: "4px",
            resize: "vertical",
          }}
        />
      )}

      {description && (
        <small style={{ color: "#888", display: "block", marginTop: "0.5em" }}>
          {description}
        </small>
      )}
    </Form.Field>
  );
};

HtmlEditor.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  required: PropTypes.bool,
  description: PropTypes.string,
};

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
        // HTML editor with WYSIWYG and source code toggle
        return (
          <HtmlEditor
            label={label}
            value={value || ""}
            onChange={(newValue) => onChange(name, newValue)}
            required={required}
            description={schema.description}
          />
        );
      }
      if (schema.format === "image") {
        // Image upload field
        const handleFileChange = (e) => {
          const file = e.target.files[0];
          if (file) {
            // For now, just store the filename - actual upload will be handled separately
            // The file will be uploaded to /static/uploads/cms/
            const filename = `uploads/cms/${file.name}`;
            onChange(name, filename);

            // Upload file to server
            const formData = new FormData();
            formData.append("file", file);
            formData.append("path", "uploads/cms");

            fetch("/data/cms/upload", {
              method: "POST",
              body: formData,
              credentials: "same-origin",
            })
              .then((response) => response.json())
              .then((data) => {
                if (data.path) {
                  onChange(name, data.path);
                }
              })
              .catch((err) => {
                console.error("Upload failed:", err);
              });
          }
        };

        const handleClear = () => {
          onChange(name, "");
        };

        return (
          <Form.Field required={required}>
            <label>{label}</label>
            {value && (
              <div style={{ marginBottom: "0.5em" }}>
                <img
                  src={`/static/${value}`}
                  alt="Preview"
                  style={{
                    maxHeight: "100px",
                    maxWidth: "200px",
                    objectFit: "contain",
                  }}
                  onError={(e) => {
                    e.target.style.display = "none";
                  }}
                />
                <div style={{ marginTop: "0.25em" }}>
                  <small style={{ color: "#666" }}>{value}</small>
                  <Button
                    icon="trash"
                    basic
                    negative
                    size="mini"
                    onClick={handleClear}
                    style={{ marginLeft: "0.5em" }}
                  />
                </div>
              </div>
            )}
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              style={{ display: "block", marginTop: "0.5em" }}
            />
            <small style={{ color: "#888" }}>
              {schema.description ||
                "Upload an image file. Leave empty to use default."}
            </small>
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
      <div className="cms-resource-header">
        <div className="cms-resource-header-content">
          <div className="cms-resource-header-info">
            <Icon
              name={getResourceIcon()}
              size="big"
              className="cms-resource-header-icon"
            />
            <div>
              <Header as="h2" className="cms-resource-header-title">
                {isNew ? "Create New" : "Edit"}{" "}
                {resourceDefinition?.label || resourceType}
              </Header>
              <p className="cms-resource-header-description">
                {resourceDefinition?.description ||
                  "Configure content settings and data"}
              </p>
            </div>
          </div>
          <span className="cms-badge">
            <Icon name={isSingleton ? "cube" : "copy"} />
            {isSingleton ? "Singleton" : "Collection"}
          </span>
        </div>
      </div>

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
              {/* Only English supported for now */}
              <div
                style={{
                  padding: "0.67857143em 1em",
                  background: "#f9f9f9",
                  border: "1px solid rgba(34,36,38,.15)",
                  borderRadius: ".28571429rem",
                  color: "rgba(0,0,0,.6)",
                }}
              >
                🇬🇧 English
              </div>
              <input type="hidden" name="lang" value="en" />
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
            className="cms-btn-primary"
            style={{
              paddingLeft: "2rem",
              paddingRight: "2rem",
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
