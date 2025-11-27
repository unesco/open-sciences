// Custom RecordsResultsListItem for UNESCO Open Science Portal
// Adds display of journal info, references count, and citations count

import { i18next } from "@translations/invenio_app_rdm/i18next";
import _get from "lodash/get";
import React, { Component } from "react";
import Overridable from "react-overridable";
import { SearchItemCreators } from "@js/invenio_app_rdm/utils";
import PropTypes from "prop-types";
import { Item, Label, Icon } from "semantic-ui-react";
import { buildUID } from "react-searchkit";
import { CompactStats } from "@js/invenio_app_rdm/components/CompactStats";
import { DisplayPartOfCommunities } from "@js/invenio_app_rdm/components/DisplayPartOfCommunities";

class CustomRecordsResultsListItem extends Component {
  render() {
    const { currentQueryState, result, key, appName } = this.props;

    const accessStatusId = _get(result, "ui.access_status.id", "open");
    const accessStatus = _get(result, "ui.access_status.title_l10n", "Open");
    const accessStatusIcon = _get(result, "ui.access_status.icon", "unlock");
    const createdDate = _get(
      result,
      "ui.created_date_l10n_long",
      i18next.t("No creation date found.")
    );

    const creators = result.ui.creators.creators;

    const descriptionStripped = _get(
      result,
      "ui.description_stripped",
      i18next.t("No description")
    );

    const publicationDate = _get(
      result,
      "ui.publication_date_l10n_long",
      i18next.t("No publication date found.")
    );
    const resourceType = _get(
      result,
      "ui.resource_type.title_l10n",
      i18next.t("No resource type")
    );
    const subjects = _get(result, "ui.subjects", []);
    const title = _get(result, "metadata.title", i18next.t("No title"));
    const version = _get(result, "ui.version", null);
    const versions = _get(result, "versions");
    const uniqueViews = _get(result, "stats.all_versions.unique_views", 0);
    const uniqueDownloads = _get(result, "stats.all_versions.unique_downloads", 0);

    const publishingInformation = _get(result, "ui.publishing_information.journal", "");

    // Custom fields extraction
    const journalInfo = _get(result, "custom_fields.journal:journal", null);
    const openAccessColour = _get(result, "custom_fields.publication:open_access_colour", null);
    
    // Parse lens:references and lens:scholarly_citations from JSON strings
    let referencesCount = 0;
    let citationsCount = 0;
    
    try {
      const referencesData = _get(result, "custom_fields.lens:references", null);
      if (referencesData) {
        const parsed = typeof referencesData === 'string' ? JSON.parse(referencesData) : referencesData;
        referencesCount = parsed.count || 0;
      }
    } catch (e) {
      console.error("Error parsing lens:references", e);
    }

    try {
      const citationsData = _get(result, "custom_fields.lens:scholarly_citations", null);
      if (citationsData) {
        const parsed = typeof citationsData === 'string' ? JSON.parse(citationsData) : citationsData;
        citationsCount = parsed.count || 0;
      }
    } catch (e) {
      console.error("Error parsing lens:scholarly_citations", e);
    }

    const filters = currentQueryState && Object.fromEntries(currentQueryState.filters);
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
        <Item key={key ?? result.id}>
          <Item.Content>
            <Item.Extra className="labels-actions">
              <Label horizontal size="small" className="primary theme-primary">
                {publicationDate} ({version})
              </Label>
              <Label horizontal size="small" className="neutral">
                {resourceType}
              </Label>
              <Label
                horizontal
                size="small"
                className={`access-status ${accessStatusId}`}
              >
                {accessStatusIcon && <Icon name={accessStatusIcon} />}
                {accessStatus}
              </Label>
              {openAccessColour && (
                <Label horizontal size="small" className="teal">
                  <Icon name="unlock" />
                  {openAccessColour}
                </Label>
              )}
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
                  <DisplayPartOfCommunities communities={result.parent?.communities} />
                  
                  {/* Journal information */}
                  {journalDisplay && (
                    <p>
                      <Icon name="book" />
                      {journalDisplay}
                    </p>
                  )}
                  
                  <p>
                    {createdDate && (
                      <>
                        {i18next.t("Uploaded on {{uploadDate}}", {
                          uploadDate: createdDate,
                        })}
                      </>
                    )}
                    {createdDate && publishingInformation && " | "}

                    {publishingInformation && (
                      <>
                        {i18next.t("Published in: {{- publishInfo }}", {
                          publishInfo: publishingInformation,
                        })}
                      </>
                    )}
                  </p>

                  {/* References and Citations counts */}
                  {(referencesCount > 0 || citationsCount > 0) && (
                    <p>
                      {referencesCount > 0 && (
                        <span style={{ marginRight: "15px" }}>
                          <Icon name="linkify" />
                          {i18next.t("{{count}} references", { count: referencesCount })}
                        </span>
                      )}
                      {citationsCount > 0 && (
                        <span>
                          <Icon name="quote right" />
                          {i18next.t("{{count}} citations", { count: citationsCount })}
                        </span>
                      )}
                    </p>
                  )}

                  {!allVersionsVisible && versions.index > 1 && (
                    <p>
                      <b>
                        {i18next.t("{{count}} more versions exist for this record", {
                          count: numOtherVersions,
                        })}
                      </b>
                    </p>
                  )}
                </small>

                <small>
                  <CompactStats
                    uniqueViews={uniqueViews}
                    uniqueDownloads={uniqueDownloads}
                  />
                </small>
              </div>
            </Item.Extra>
          </Item.Content>
        </Item>
      </Overridable>
    );
  }
}

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
