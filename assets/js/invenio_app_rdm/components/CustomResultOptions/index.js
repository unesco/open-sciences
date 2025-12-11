// Custom ResultOptions component with Download XLSX button
// Positioned to the left of Sort by

import React, { useContext, useState } from "react";
import Overridable from "react-overridable";
import { Count, LayoutSwitcher, Sort } from "react-searchkit";
import { Grid, Button, Icon } from "semantic-ui-react";
import { SearchConfigurationContext } from "@js/invenio_search_ui/components/context";
import { i18next } from "@translations/invenio_search_ui/i18next";
import { AppMedia } from "@js/invenio_theme/Media";

// Function to trigger download from backend API
const downloadXLSX = async (setLoading) => {
  setLoading(true);
  try {
    // Get current URL search params to pass to the export endpoint
    const currentParams = new URLSearchParams(window.location.search);

    // Build export URL with same parameters
    const exportUrl = `/data/export?${currentParams.toString()}`;

    // Use fetch to download the file
    const response = await fetch(exportUrl);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Export failed");
    }

    // Get the blob from response
    const blob = await response.blob();

    // Create download link
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;

    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get("Content-Disposition");
    let filename = `unesco_export_${
      new Date().toISOString().split("T")[0]
    }.xlsx`;
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?([^"]+)"?/);
      if (match) filename = match[1];
    }

    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Export error:", error);
    alert(`Error downloading results: ${error.message}`);
  } finally {
    setLoading(false);
  }
};

// This component receives props from the Overridable wrapper
export const CustomResultOptions = ({
  currentResultsState,
  sortOptions,
  paginationOptions,
  layoutOptions,
}) => {
  const { MediaContextProvider, Media } = AppMedia;
  const { sortOrderDisabled, buildUID } = useContext(
    SearchConfigurationContext
  );
  const multipleLayouts = layoutOptions?.listView && layoutOptions?.gridView;
  const [isLoading, setIsLoading] = useState(false);
  const totalResults = currentResultsState?.data?.total || 0;

  const handleDownload = () => {
    if (totalResults === 0) {
      alert("No results to download");
      return;
    }
    downloadXLSX(setIsLoading);
  };

  return (
    <MediaContextProvider>
      <Grid>
        <Grid.Row verticalAlign="middle">
          <Grid.Column
            at="mobile"
            as={Media}
            textAlign="right"
            width={16}
            floated="right"
            className="mb-10"
          >
            <Count
              label={(cmp) => (
                <>
                  {cmp} {i18next.t("result(s) found")}
                </>
              )}
            />
          </Grid.Column>
          <Grid.Column
            as={Media}
            greaterThanOrEqual="tablet"
            textAlign="left"
            width={multipleLayouts ? 5 : 8}
            className="mb-10"
          >
            <Count
              label={(cmp) => (
                <>
                  {cmp} {i18next.t("result(s) found")}
                </>
              )}
            />
          </Grid.Column>

          <Grid.Column computer={8} tablet={8} mobile={16} textAlign="right">
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-end",
                gap: "16px",
              }}
            >
              {/* Download XLSX Button */}
              <style>
                {`
                  .unesco-download-btn.ui.button,
                  .unesco-download-btn.ui.button:not(.basic):not(.transparent):not(.jump-to-top):not(.labeled):not(.search) {
                    border-radius: 20px !important;
                    background-color: transparent !important;
                    border: 1px solid #0077D4 !important;
                    color: #0077D4 !important;
                    box-shadow: none !important;
                  }
                  .unesco-download-btn.ui.button:hover {
                    background-color: rgba(0, 119, 212, 0.1) !important;
                  }
                  .unesco-download-btn.ui.button.loading {
                    pointer-events: none;
                    opacity: 0.7;
                  }
                `}
              </style>
              <Button
                className={`unesco-download-btn ${isLoading ? "loading" : ""}`}
                compact
                onClick={handleDownload}
                disabled={isLoading || totalResults === 0}
                title="Download current page results as Excel (XLSX)"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  backgroundColor: "transparent",
                  border: "1px solid #0077D4",
                  color: "#0077D4",
                  padding: "10px 20px",
                  fontWeight: 500,
                  height: "38px",
                  boxSizing: "border-box",
                }}
              >
                {isLoading ? "Downloading..." : "Download"}
                <Icon
                  name={isLoading ? "spinner" : "download"}
                  loading={isLoading}
                  style={{ margin: 0 }}
                />
              </Button>

              {/* Sort by */}
              {sortOptions && (
                <div
                  className="unesco-sort-wrapper"
                  style={{ display: "flex", alignItems: "center", gap: "8px" }}
                >
                  <label
                    style={{
                      color: "#212121",
                      fontWeight: 400,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {i18next.t("Sort by:")}
                  </label>
                  <div
                    style={{
                      "--dropdown-border-radius": "20px",
                    }}
                  >
                    <style>
                      {`
                        .unesco-sort-wrapper .ui.selection.dropdown {
                          border-radius: 20px !important;
                          min-height: 38px !important;
                          padding: 10px 16px !important;
                        }
                        .unesco-sort-wrapper .ui.selection.dropdown .menu {
                          border-radius: 12px !important;
                        }
                      `}
                    </style>
                    <Sort
                      sortOrderDisabled={sortOrderDisabled || false}
                      values={sortOptions}
                      ariaLabel={i18next.t("Sort")}
                      label={(cmp) => cmp}
                    />
                  </div>
                </div>
              )}
            </div>
          </Grid.Column>
          {multipleLayouts ? (
            <Grid.Column width={3} textAlign="right">
              <LayoutSwitcher />
            </Grid.Column>
          ) : null}
        </Grid.Row>
      </Grid>
    </MediaContextProvider>
  );
};

export default CustomResultOptions;
