// Custom RecordsResultsListItem for UNESCO Open Science Portal
// Adds display of journal info, references count, and citations count

import { i18next } from "@translations/invenio_app_rdm/i18next";
import _get from "lodash/get";
import React from "react";
import Overridable from "react-overridable";
import { SearchItemCreators } from "@js/invenio_app_rdm/utils";
import PropTypes from "prop-types";
import { Item, Label, Icon } from "semantic-ui-react";
import { buildUID } from "react-searchkit";
import { DisplayPartOfCommunities } from "@js/invenio_app_rdm/components/DisplayPartOfCommunities";

const CustomRecordsResultsListItem = ({
  currentQueryState,
  result,
  key,
  appName,
}) => {
  const accessStatusId = _get(result, "ui.access_status.id", "open");
  const accessStatus = _get(result, "ui.access_status.title_l10n", "Open");
  const accessStatusIcon = _get(result, "ui.access_status.icon", "unlock");
  const createdDate = _get(
    result,
    "ui.created_date_l10n_long",
    i18next.t("No creation date found."),
  );

  const creators = result.ui.creators.creators;

  const descriptionStripped = _get(
    result,
    "ui.description_stripped",
    i18next.t("No description"),
  );

  const publicationDate = _get(
    result,
    "ui.publication_date_l10n_long",
    i18next.t("No publication date found."),
  );
  const resourceType = _get(
    result,
    "ui.resource_type.title_l10n",
    i18next.t("No resource type"),
  );
  const subjects = _get(result, "ui.subjects", []);
  const title = _get(result, "metadata.title", i18next.t("No title"));
  const version = _get(result, "ui.version", null);
  const versions = _get(result, "versions");

  const publishingInformation = _get(
    result,
    "ui.publishing_information.journal",
    "",
  );

  // Custom fields extraction
  const journalInfo = _get(result, "custom_fields.journal:journal", null);
  const isOpenAccess = _get(
    result,
    "custom_fields.publication:is_open_access",
    null,
  );
  const openAccessColour = _get(
    result,
    "custom_fields.publication:open_access_colour",
    null,
  );

  // Extract views count from stats
  const viewsCount = _get(result, "stats.all_versions.unique_views", 0);

  // Parse lens:references and lens:scholarly_citations from JSON strings
  let referencesCount = 0;
  let scholarlyCitationsCount = 0;
  let patentCitationsCount = 0;

  try {
    const referencesData = _get(result, "custom_fields.lens:references", null);
    if (referencesData) {
      const parsed =
        typeof referencesData === "string"
          ? JSON.parse(referencesData)
          : referencesData;
      referencesCount = parsed.count || 0;
    }
  } catch (e) {
    console.error("Error parsing lens:references", e);
  }

  try {
    const citationsData = _get(
      result,
      "custom_fields.lens:scholarly_citations",
      null,
    );
    if (citationsData) {
      const parsed =
        typeof citationsData === "string"
          ? JSON.parse(citationsData)
          : citationsData;
      scholarlyCitationsCount = parsed.count || 0;
    }
  } catch (e) {
    console.error("Error parsing lens:scholarly_citations", e);
  }

  try {
    const patentData = _get(
      result,
      "custom_fields.lens:patent_citations",
      null,
    );
    if (patentData) {
      const parsed =
        typeof patentData === "string" ? JSON.parse(patentData) : patentData;
      patentCitationsCount = parsed.count || 0;
    }
  } catch (e) {
    console.error("Error parsing lens:patent_citations", e);
  }

  const filters =
    currentQueryState && Object.fromEntries(currentQueryState.filters);
  const allVersionsVisible = filters?.allversions;
  const numOtherVersions = versions.index - 1;

  // Derivatives
  const viewLink = `/records/${result.id}`;

  // Build journal display string
  let journalDisplay = "";
  if (journalInfo) {
    const parts = [];
    if (journalInfo.title) parts.push(journalInfo.title);
    if (journalInfo.volume) parts.push(`Vol. ${journalInfo.volume}`);
    if (journalInfo.issue) parts.push(`Issue ${journalInfo.issue}`);
    if (journalInfo.pages) parts.push(`pp. ${journalInfo.pages}`);
    journalDisplay = parts.join(", ");
  }

  return (
    <Overridable
      id={buildUID("RecordsResultsListItem.layout", "", appName)}
      result={result}
      key={key}
      accessStatusId={accessStatusId}
      accessStatus={accessStatus}
      accessStatusIcon={accessStatusIcon}
      createdDate={createdDate}
      creators={creators}
      descriptionStripped={descriptionStripped}
      publicationDate={publicationDate}
      resourceType={resourceType}
      subjects={subjects}
      title={title}
      version={version}
      versions={versions}
      allVersionsVisible={allVersionsVisible}
      numOtherVersions={numOtherVersions}
    >
      <Item
        key={key ?? result.id}
        className="unesco-search-result-item"
        style={{ marginTop: 0, paddingTop: "12px" }}
      >
        <Item.Content>
          <Item.Extra
            className="unesco-tags-row"
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "8px",
              marginBottom: "12px",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              <span
                className="unesco-tag unesco-tag-date"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  padding: "6px 12px",
                  backgroundColor: "#CEE9FF",
                  color: "#212121",
                  borderRadius: "4px",
                  fontSize: "14px",
                  fontWeight: "600",
                }}
              >
                {publicationDate}
              </span>
              <span
                className="unesco-tag unesco-tag-type"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  padding: "6px 12px",
                  backgroundColor: "#F1F4F6",
                  color: "#4C5054",
                  borderRadius: "4px",
                  fontSize: "14px",
                  fontWeight: "600",
                }}
              >
                {resourceType}
              </span>
              {accessStatusId !== "metadata-only" && (
                <span
                  className={`unesco-tag unesco-tag-access-${accessStatusId}`}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    padding: "6px 12px",
                    backgroundColor:
                      accessStatusId === "open"
                        ? "#4FB293"
                        : accessStatusId === "embargoed"
                          ? "#F39C12"
                          : accessStatusId === "restricted"
                            ? "#E74C3C"
                            : "#F1F4F6",
                    color: "#FFFFFF",
                    borderRadius: "4px",
                    fontSize: "14px",
                    fontWeight: "400",
                    gap: "6px",
                  }}
                >
                  {accessStatusIcon && (
                    <Icon
                      name={accessStatusIcon}
                      style={{
                        margin: 0,
                        display: "flex",
                        alignItems: "center",
                      }}
                    />
                  )}
                  {accessStatus}
                </span>
              )}
              {isOpenAccess === "true" && (
                <span
                  className="unesco-tag unesco-tag-open-access"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    padding: "6px 12px",
                    backgroundColor: "#4FB293",
                    color: "#FFFFFF",
                    borderRadius: "4px",
                    fontSize: "14px",
                    fontWeight: "400",
                    gap: "6px",
                  }}
                >
                  <Icon
                    name="unlock"
                    style={{ margin: 0, display: "flex", alignItems: "center" }}
                  />
                  Open Access
                </span>
              )}
            </div>
            {/* <span
              className="unesco-views-count"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                fontSize: "12px",
                color: "#6C757D",
                fontWeight: "400",
                marginLeft: "auto",
              }}
            >
              <Icon
                name="eye"
                style={{ margin: 0, display: "flex", alignItems: "center" }}
              />
              <span>{viewsCount.toLocaleString()}</span>
            </span> */}
          </Item.Extra>
          <Item.Header as="h2" className="theme-primary-text">
            <a href={viewLink}>{title}</a>
          </Item.Header>
          <Item className="creatibutors">
            <SearchItemCreators creators={creators} othersLink={viewLink} />
          </Item>
          <Overridable
            id={buildUID("RecordsResultsListItem.description", "", appName)}
            descriptionStripped={descriptionStripped}
            result={result}
          >
            <Item.Description className="truncate-lines-2">
              {descriptionStripped}
            </Item.Description>
          </Overridable>

          <Item.Extra>
            {subjects.map((subject) => (
              <Label key={subject.title_l10n} size="tiny">
                {subject.title_l10n}
              </Label>
            ))}

            <div className="flex justify-space-between align-items-end">
              <small>
                <DisplayPartOfCommunities
                  communities={result.parent?.communities}
                />

                {/* Journal information */}
                {journalDisplay && (
                  <span
                    className="unesco-journal-item"
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "8px",
                      fontSize: "14px",
                      color: "#212121",
                      marginTop: "12px",
                    }}
                  >
                    <Icon
                      name="book"
                      style={{
                        margin: 0,
                        display: "flex",
                        alignItems: "center",
                      }}
                    />
                    <span>{journalDisplay}</span>
                  </span>
                )}

                {/* Citations counts - Patents and Scholarly Works side by side */}
                {(patentCitationsCount > 0 ||
                  scholarlyCitationsCount > 0 ||
                  referencesCount > 0) && (
                  <div
                    className="unesco-citations-row"
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: "32px",
                      marginTop: "12px",
                      alignItems: "center",
                    }}
                  >
                    {patentCitationsCount > 0 && (
                      <span
                        className="unesco-citation-item"
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "8px",
                          fontSize: "14px",
                          color: "#212121",
                        }}
                      >
                        <Icon
                          name="file alternate outline"
                          style={{
                            margin: 0,
                            display: "flex",
                            alignItems: "center",
                          }}
                        />
                        <span>Cited by patents: {patentCitationsCount}</span>
                      </span>
                    )}
                    {scholarlyCitationsCount > 0 && (
                      <span
                        className="unesco-citation-item"
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "8px",
                          fontSize: "14px",
                          color: "#212121",
                        }}
                      >
                        <Icon
                          name="quote right"
                          style={{
                            margin: 0,
                            display: "flex",
                            alignItems: "center",
                          }}
                        />
                        <span>
                          Cited by scholarly works: {scholarlyCitationsCount}
                        </span>
                      </span>
                    )}
                    {referencesCount > 0 && (
                      <span
                        className="unesco-citation-item"
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "8px",
                          fontSize: "14px",
                          color: "#212121",
                        }}
                      >
                        <Icon
                          name="linkify"
                          style={{
                            margin: 0,
                            display: "flex",
                            alignItems: "center",
                          }}
                        />
                        <span>References: {referencesCount}</span>
                      </span>
                    )}
                  </div>
                )}

                {!allVersionsVisible && versions.index > 1 && (
                  <p>
                    <b>
                      {i18next.t(
                        "{{count}} more versions exist for this record",
                        {
                          count: numOtherVersions,
                        },
                      )}
                    </b>
                  </p>
                )}
              </small>
            </div>
          </Item.Extra>
        </Item.Content>
      </Item>
    </Overridable>
  );
};

CustomRecordsResultsListItem.propTypes = {
  currentQueryState: PropTypes.object,
  result: PropTypes.object.isRequired,
  key: PropTypes.string,
  appName: PropTypes.string,
};

CustomRecordsResultsListItem.defaultProps = {
  key: null,
  currentQueryState: null,
  appName: "",
};

export default CustomRecordsResultsListItem;
