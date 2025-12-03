// Custom facets component for InvenioRDM
// Replaces the default SearchApp.facets with custom dynamic filters

import React, { Component } from "react";
import PropTypes from "prop-types";
import DynamicFacet from "./DynamicFacet";
import UnescoToggleFacet from "./facets/UnescoToggleFacet";
import OpenAccessToggleFacet from "./facets/OpenAccessToggleFacet";

// Main custom facets component
export class CustomFacets extends Component {
  render() {
    const { aggs, appName } = this.props;

    return (
      <>
        {/* Custom dynamic facets using reusable DynamicFacet component */}
        <DynamicFacet
          label="Author"
          apiField="author"
          queryField="metadata.creators.person_or_org.name"
          placeholder="Search authors..."
          icon="user"
          maxResults={100}
        />
        <DynamicFacet
          label="Subject / Keyword"
          apiField="subject"
          queryField="metadata.subjects.subject"
          placeholder="Search subjects..."
          icon="tags"
          maxResults={100}
        />
        <DynamicFacet
          label="Affiliation"
          apiField="affiliation"
          queryField="metadata.creators.affiliations.name"
          placeholder="Search affiliations..."
          icon="building"
          maxResults={100}
        />
        <DynamicFacet
          label="Country"
          apiField="country"
          queryField="metadata.custom_fields.country"
          placeholder="Search countries..."
          icon="globe"
          maxResults={100}
          useFacetParameter={true}
          facetName="publication_country"
        />
        <DynamicFacet
          label="Funding Organization"
          apiField="funding"
          queryField="metadata.funding.funder.name"
          placeholder="Search funding organizations..."
          icon="money"
          maxResults={100}
          useFacetParameter={true}
          facetName="funding_org"
        />
        <DynamicFacet
          label="Resource Type"
          apiField="resource_type"
          queryField="metadata.resource_type.id"
          placeholder="Search resource types..."
          icon="file alternate"
          maxResults={50}
          useFacetParameter={true}
          facetName="resource_type"
        />
        <DynamicFacet
          label="Publication Year"
          apiField="year"
          queryField="metadata.publication_date"
          placeholder="Search years..."
          icon="calendar"
          maxResults={50}
          useFacetParameter={true}
          facetName="publication_year"
        />
        <UnescoToggleFacet />
        <OpenAccessToggleFacet />
      </>
    );
  }
}

CustomFacets.propTypes = {
  aggs: PropTypes.array,
  appName: PropTypes.string,
};

CustomFacets.defaultProps = {
  aggs: [],
  appName: "",
};

export default CustomFacets;
