/**
 * CMS Page Component
 * Administration interface for Resource-Driven content management
 */

import React, { useState, useCallback } from "react";
import PropTypes from "prop-types";
import { Breadcrumb, Icon } from "semantic-ui-react";

// Import components individually to catch import errors
import { ResourceList } from "./components/ResourceList";
import { ContentList } from "./components/ContentList";
import { ContentEditor } from "./components/ContentEditor";

/**
 * Main Resource CMS Admin Component
 * Manages state for active resource type and edit modes
 */
export const ResourceCMS = ({ apiEndpoint = "/data/cms" }) => {
  // Current view state
  const [currentView, setCurrentView] = useState("resources"); // "resources" | "content" | "editor"

  // Selected resource type
  const [selectedResource, setSelectedResource] = useState(null);
  const [resourceDefinition, setResourceDefinition] = useState(null);

  // Content being edited
  const [editingContent, setEditingContent] = useState(null);

  // Refresh counter
  const [refreshKey, setRefreshKey] = useState(0);

  // Handle resource selection
  const handleSelectResource = useCallback((resourceType, definition) => {
    setSelectedResource(resourceType);
    setResourceDefinition(definition);
    setCurrentView("content");
  }, []);

  // Handle back to resource list
  const handleBackToResources = useCallback(() => {
    setSelectedResource(null);
    setResourceDefinition(null);
    setEditingContent(null);
    setCurrentView("resources");
  }, []);

  // Handle edit content
  const handleEditContent = useCallback((content) => {
    setEditingContent(content);
    setCurrentView("editor");
  }, []);

  // Handle save content
  const handleSaveContent = useCallback((savedContent) => {
    setEditingContent(null);
    setCurrentView("content");
    setRefreshKey((prev) => prev + 1);
  }, []);

  // Handle cancel edit
  const handleCancelEdit = useCallback(() => {
    setEditingContent(null);
    setCurrentView("content");
  }, []);

  // Render breadcrumb navigation
  const renderBreadcrumb = () => {
    if (currentView === "resources") return null;

    return (
      <div className="cms-breadcrumb">
        <Breadcrumb size="small">
          <Breadcrumb.Section link onClick={handleBackToResources}>
            <Icon name="home" /> Content Types
          </Breadcrumb.Section>

          {selectedResource && (
            <>
              <Breadcrumb.Divider icon="right chevron" />
              <Breadcrumb.Section
                link={currentView === "editor"}
                active={currentView === "content"}
                onClick={
                  currentView === "editor"
                    ? () => setCurrentView("content")
                    : undefined
                }
              >
                {resourceDefinition?.label || selectedResource}
              </Breadcrumb.Section>
            </>
          )}

          {currentView === "editor" && (
            <>
              <Breadcrumb.Divider icon="right chevron" />
              <Breadcrumb.Section active>
                {editingContent ? "Edit" : "New"}
              </Breadcrumb.Section>
            </>
          )}
        </Breadcrumb>
      </div>
    );
  };

  // Render active content based on view
  const renderContent = () => {
    switch (currentView) {
      case "resources":
        return <ResourceList onSelectResource={handleSelectResource} />;

      case "content":
        return (
          <ContentList
            resourceType={selectedResource}
            resourceDefinition={resourceDefinition}
            onEdit={handleEditContent}
            onBack={handleBackToResources}
            refreshKey={refreshKey}
          />
        );

      case "editor":
        return (
          <ContentEditor
            resourceType={selectedResource}
            resourceDefinition={resourceDefinition}
            content={editingContent}
            onSave={handleSaveContent}
            onCancel={handleCancelEdit}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="resource-cms-admin" style={{ padding: "0.5rem 0" }}>
      {/* Breadcrumb navigation */}
      {renderBreadcrumb()}

      {/* Main content area */}
      <div className="cms-content">{renderContent()}</div>
    </div>
  );
};

ResourceCMS.propTypes = {
  apiEndpoint: PropTypes.string,
};

// Also export as CMS for convenience
export const CMS = ResourceCMS;

// Re-export components for direct access if needed
export { ResourceList, ContentList, ContentEditor };
export { default as ConfirmModal } from "./components/ConfirmModal";

// Re-export hooks
export { useResourceCMSApi, useDebounce } from "./hooks";

export default ResourceCMS;
