// Custom ResultOptions component with Download CSV button
// Positioned to the left of Sort by

import React, { useContext } from "react";
import Overridable from "react-overridable";
import { Count, LayoutSwitcher, Sort } from "react-searchkit";
import { Grid, Button, Icon } from "semantic-ui-react";
import { SearchConfigurationContext } from "@js/invenio_search_ui/components/context";
import { i18next } from "@translations/invenio_search_ui/i18next";
import { AppMedia } from "@js/invenio_theme/Media";

// Function to convert results to CSV
const convertToCSV = (results) => {
  if (!results || results.length === 0) return "";

  // Define CSV headers
  const headers = [
    "Title",
    "Authors",
    "Publication Date",
    "Resource Type",
    "DOI",
    "Access Status",
    "Description",
    "Subjects",
  ];

  // Map results to CSV rows
  const rows = results.map((record) => {
    const metadata = record.metadata || {};
    const ui = record.ui || {};

    // Extract authors
    const authors = (metadata.creators || [])
      .map((c) => c.person_or_org?.name || "")
      .filter(Boolean)
      .join("; ");

    // Extract subjects
    const subjects = (ui.subjects || [])
      .map((s) => s.title_l10n || s.subject || "")
      .filter(Boolean)
      .join("; ");

    // Extract DOI
    const doi = record.pids?.doi?.identifier || "";

    // Escape CSV values
    const escapeCSV = (value) => {
      if (!value) return "";
      const str = String(value);
      if (str.includes(",") || str.includes('"') || str.includes("\n")) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    };

    return [
      escapeCSV(metadata.title),
      escapeCSV(authors),
      escapeCSV(ui.publication_date_l10n_long || metadata.publication_date),
      escapeCSV(ui.resource_type?.title_l10n || ""),
      escapeCSV(doi),
      escapeCSV(ui.access_status?.title_l10n || ""),
      escapeCSV(ui.description_stripped || ""),
      escapeCSV(subjects),
    ].join(",");
  });

  // Combine headers and rows
  return [headers.join(","), ...rows].join("\n");
};

// Function to download CSV
const downloadCSV = (results) => {
  const csv = convertToCSV(results);
  if (!csv) {
    alert("No results to download");
    return;
  }

  // Create blob and download
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute(
    "download",
    `search-results-${new Date().toISOString().split("T")[0]}.csv`
  );
  link.style.visibility = "hidden";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
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
  const hits = currentResultsState?.data?.hits || [];

  const handleDownload = () => {
    downloadCSV(hits);
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
              {/* Download CSV Button */}
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
                `}
              </style>
              <Button
                className="unesco-download-btn"
                compact
                onClick={handleDownload}
                title="Download current page results as CSV"
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
                Download
                <Icon name="download" style={{ margin: 0 }} />
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
