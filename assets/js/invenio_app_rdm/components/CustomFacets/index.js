// Custom facets component for InvenioRDM
// Replaces the default SearchApp.facets with custom dynamic filters

import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import {
  DynamicFacet,
  UnescoToggleFacet,
  OpenAccessToggleFacet,
  ResourceTypeFacet,
} from "./components";

// Main custom facets component
export const CustomFacets = ({ aggs, appName }) => {
  // Force re-render when URL changes (e.g., when "Start over" is clicked)
  const [urlKey, setUrlKey] = useState(window.location.search);
  const [resultsLoaded, setResultsLoaded] = useState(false);

  useEffect(() => {
    // Listen for URL changes (browser back/forward, Start over button, etc.)
    const handleUrlChange = () => {
      setUrlKey(window.location.search);
    };

    // Listen to popstate event (browser navigation)
    window.addEventListener("popstate", handleUrlChange);

    // Also check periodically for URL changes (for programmatic navigation)
    const intervalId = setInterval(() => {
      if (window.location.search !== urlKey) {
        setUrlKey(window.location.search);
      }
    }, 500);

    return () => {
      window.removeEventListener("popstate", handleUrlChange);
      clearInterval(intervalId);
    };
  }, [urlKey]);

  // Monitor when results are loaded
  useEffect(() => {
    const checkResults = () => {
      const resultsExist = document.querySelector('.divided.items .item') !== null;
      setResultsLoaded(resultsExist);
    };

    // Check immediately
    checkResults();

    // Set up a MutationObserver to watch for DOM changes
    const observer = new MutationObserver(checkResults);
    const targetNode = document.querySelector('.relaxed.grid');
    if (targetNode) {
      observer.observe(targetNode, { childList: true, subtree: true });
    }

    // Also check periodically as fallback
    const intervalId = setInterval(checkResults, 300);

    return () => {
      observer.disconnect();
      clearInterval(intervalId);
    };
  }, [urlKey]);

  return (
    <>
      <style>
        {`
          /* Align facets container with Sort by row - only when results are loaded */
          /* Only apply on desktop/tablet (computer only column), not mobile */
          @media (min-width: 768px) {
            .computer.only.column .custom-facets-container.results-loaded {
              margin-top: -58px;
            }
          }
        `}
      </style>
      <div 
        className={`custom-facets-container ${resultsLoaded ? 'results-loaded' : ''}`} 
        style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}
      >
      <OpenAccessToggleFacet key={`open-access-${urlKey}`} />
      <ResourceTypeFacet key={`resource-type-${urlKey}`} />
      <DynamicFacet
        key={`author-${urlKey}`}
        label="Author"
        apiField="author"
        queryField="metadata.creators.person_or_org.name"
        placeholder="Search authors..."
        icon="user"
        maxResults={100}
      />
      <DynamicFacet
        key={`affiliation-${urlKey}`}
        label="Author Affiliation"
        apiField="affiliation"
        queryField="metadata.creators.affiliations.name"
        placeholder="Search affiliations..."
        icon="building"
        maxResults={100}
      />
      <DynamicFacet
        key={`country-${urlKey}`}
        label="Author Affiliation Country"
        apiField="country"
        queryField="metadata.custom_fields.country"
        placeholder="Search countries..."
        icon="globe"
        maxResults={100}
        useFacetParameter={true}
        facetName="publication_country"
      />
      <DynamicFacet
        key={`subject-${urlKey}`}
        label="Subject / Keyword"
        apiField="subject"
        queryField="metadata.subjects.subject"
        placeholder="Search subjects..."
        icon="tags"
        maxResults={100}
      />
      <DynamicFacet
        key={`funding-${urlKey}`}
        label="Funding"
        apiField="funding"
        queryField="metadata.funding.funder.name"
        placeholder="Search funding organizations..."
        icon="money"
        maxResults={100}
        useFacetParameter={true}
        facetName="funding_org"
      />
      <DynamicFacet
        key={`year-${urlKey}`}
        label="Publication Year"
        apiField="year"
        queryField="metadata.publication_date"
        placeholder="Search years..."
        icon="calendar"
        maxResults={50}
        useFacetParameter={true}
        facetName="publication_year"
      />
      <UnescoToggleFacet key={`unesco-${urlKey}`} />
    </div>
    </>
  );
};

CustomFacets.propTypes = {
  aggs: PropTypes.array,
  appName: PropTypes.string,
};

CustomFacets.defaultProps = {
  aggs: [],
  appName: "",
};

export default CustomFacets;
