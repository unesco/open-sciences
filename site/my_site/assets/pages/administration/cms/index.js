/**
 * CMS Page Component
 * Administration interface for content management
 */

import React, { useState, useCallback } from "react";
import PropTypes from "prop-types";

// Sub-components
import {
  PageList,
  PageEditor,
  CategoryList,
  CategoryEditor,
  CMSNavigation,
} from "./components";

/**
 * Main CMS Admin Component
 * Manages state for active view and edit modes
 */
export const CMS = ({ apiEndpoint = "/api/cms" }) => {
  // Active view: "pages" or "categories"
  const [activeView, setActiveView] = useState("pages");

  // Edit mode states
  const [editingPage, setEditingPage] = useState(null);
  const [isEditingPage, setIsEditingPage] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [isEditingCategory, setIsEditingCategory] = useState(false);

  // Refresh counters (to trigger re-fetch)
  const [refreshKey, setRefreshKey] = useState(0);

  // Handle view change
  const handleViewChange = useCallback((view) => {
    // Reset edit modes when switching views
    setIsEditingPage(false);
    setEditingPage(null);
    setIsEditingCategory(false);
    setEditingCategory(null);
    setActiveView(view);
  }, []);

  // Page handlers
  const handleEditPage = useCallback((page) => {
    setEditingPage(page);
    setIsEditingPage(true);
  }, []);

  const handleSavePage = useCallback((savedPage) => {
    // Go back to list after successful save
    setIsEditingPage(false);
    setEditingPage(null);
    setRefreshKey((prev) => prev + 1);
  }, []);

  const handleCancelPageEdit = useCallback(() => {
    setIsEditingPage(false);
    setEditingPage(null);
  }, []);

  // Category handlers
  const handleEditCategory = useCallback((category) => {
    setEditingCategory(category);
    setIsEditingCategory(true);
  }, []);

  const handleSaveCategory = useCallback((savedCategory) => {
    // Go back to list after successful save
    setIsEditingCategory(false);
    setEditingCategory(null);
    setRefreshKey((prev) => prev + 1);
  }, []);

  const handleCancelCategoryEdit = useCallback(() => {
    setIsEditingCategory(false);
    setEditingCategory(null);
  }, []);

  // Refresh handler
  const handleRefresh = useCallback(() => {
    setRefreshKey((prev) => prev + 1);
  }, []);

  // Render active content based on view and edit mode
  const renderContent = () => {
    if (activeView === "pages") {
      if (isEditingPage) {
        return (
          <PageEditor
            page={editingPage}
            onSave={handleSavePage}
            onCancel={handleCancelPageEdit}
          />
        );
      }
      return (
        <PageList
          key={`pages-${refreshKey}`}
          onEdit={handleEditPage}
          onRefresh={handleRefresh}
        />
      );
    }

    if (activeView === "categories") {
      if (isEditingCategory) {
        return (
          <CategoryEditor
            category={editingCategory}
            onSave={handleSaveCategory}
            onCancel={handleCancelCategoryEdit}
          />
        );
      }
      return (
        <CategoryList
          key={`categories-${refreshKey}`}
          onEdit={handleEditCategory}
          onRefresh={handleRefresh}
        />
      );
    }

    return null;
  };

  return (
    <div className="cms-admin">
      {/* Navigation tabs */}
      {!isEditingPage && !isEditingCategory && (
        <CMSNavigation
          activeView={activeView}
          onViewChange={handleViewChange}
        />
      )}

      {/* Main content area */}
      <div className="cms-content">{renderContent()}</div>
    </div>
  );
};

CMS.propTypes = {
  apiEndpoint: PropTypes.string,
};
