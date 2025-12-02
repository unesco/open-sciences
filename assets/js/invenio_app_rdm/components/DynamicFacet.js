// Generic reusable facet component for InvenioRDM
// Can be used for Author, Subject, Affiliation, Funding, etc.

import React, { Component } from "react";
import { Card, Dropdown, Label, Button } from "semantic-ui-react";
import PropTypes from "prop-types";
import _debounce from "lodash/debounce";

class DynamicFacet extends Component {
  constructor(props) {
    super(props);

    // Parse current URL to get selected value
    const selectedValue = this.getSelectedValueFromURL();

    this.state = {
      loading: false,
      searchQuery: "",
      options: [],
      selectedValue: selectedValue,
    };

    // Debounce search to avoid too many API calls
    this.debouncedSearch = _debounce(this.fetchOptions.bind(this), 300);
  }

  componentDidMount() {
    const { selectedValue } = this.state;

    // If there's a selected value from URL, add it to options first
    if (selectedValue) {
      this.setState({
        options: [
          {
            key: selectedValue,
            text: selectedValue,
            value: selectedValue,
            content: (
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span>{selectedValue}</span>
              </div>
            ),
          },
        ],
      });
    }

    // Load initial options
    this.fetchOptions("");
  }

  getSelectedValueFromURL() {
    const { queryField } = this.props;
    const searchParams = new URLSearchParams(window.location.search);
    const currentQuery = searchParams.get("q") || "";

    // Escape dots in field name for regex
    const escapedField = queryField.replace(/\./g, "\\.");
    const regex = new RegExp(`${escapedField}:"([^"]+)"`);
    const match = currentQuery.match(regex);

    return match ? match[1] : null;
  }

  fetchOptions(query) {
    const { apiField, maxResults } = this.props;
    this.setState({ loading: true });

    const url = `/data/search?field=${apiField}${
      query ? `&q=${encodeURIComponent(query)}` : ""
    }&size=${maxResults}&sort=count`;

    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        const results = data.results || [];
        const newOptions = results.map((item) => ({
          key: item.value,
          text: item.value,
          value: item.value,
          count: item.count,
          content: (
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>{item.value}</span>
              <Label size="mini" circular>
                {item.count}
              </Label>
            </div>
          ),
        }));

        this.setState({
          options: newOptions,
          loading: false,
          searchQuery: query,
        });
      })
      .catch((error) => {
        console.error(`Error fetching ${this.props.label}:`, error);
        this.setState({
          loading: false,
        });
      });
  }

  handleSearchChange = (e, { searchQuery }) => {
    this.setState({ searchQuery, options: [] });
    this.debouncedSearch(searchQuery);
  };

  handleChange = (e, { value }) => {
    const { queryField } = this.props;
    this.setState({ selectedValue: value });

    // Build the search query and redirect
    const searchParams = new URLSearchParams(window.location.search);
    const existingQuery = searchParams.get("q") || "";

    // Parse existing filters from query
    const filters = {};
    const filterRegex = /([^\s:]+(?:\.[^\s:]+)*):"([^"]+)"/g;
    let match;
    while ((match = filterRegex.exec(existingQuery)) !== null) {
      filters[match[1]] = match[2];
    }

    // Update or remove current filter
    if (value) {
      filters[queryField] = value;
    } else {
      delete filters[queryField];
    }

    // Rebuild composite query with AND operators
    const queryParts = Object.entries(filters).map(
      ([field, val]) => `${field}:"${val}"`
    );

    if (queryParts.length > 0) {
      searchParams.set("q", queryParts.join(" AND "));
    } else {
      searchParams.delete("q");
    }

    window.location.href = `/search?${searchParams.toString()}`;
  };

  clearFilter = () => {
    this.setState({ selectedValue: null });
    const searchParams = new URLSearchParams(window.location.search);
    const existingQuery = searchParams.get("q") || "";
    const { queryField } = this.props;

    // Parse existing filters
    const filters = {};
    const filterRegex = /([^\s:]+(?:\.[^\s:]+)*):"([^"]+)"/g;
    let match;
    while ((match = filterRegex.exec(existingQuery)) !== null) {
      filters[match[1]] = match[2];
    }

    // Remove only this filter
    delete filters[queryField];

    // Rebuild query
    const queryParts = Object.entries(filters).map(
      ([field, val]) => `${field}:"${val}"`
    );

    if (queryParts.length > 0) {
      searchParams.set("q", queryParts.join(" AND "));
    } else {
      searchParams.delete("q");
    }

    window.location.href = `/search?${searchParams.toString()}`;
  };

  render() {
    const { loading, options, selectedValue } = this.state;
    const { label, placeholder, icon } = this.props;

    return (
      <Card
        className="borderless facet"
        style={{ overflow: "visible", position: "relative", zIndex: "auto" }}
      >
        <Card.Content style={{ overflow: "visible" }}>
          <Card.Header
            as="h2"
            style={{
              color: "#2185d0",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <span style={{ display: "flex", alignItems: "center" }}>
              {icon && (
                <i
                  className={`${icon} icon`}
                  style={{ marginRight: "8px", color: "#2185d0" }}
                ></i>
              )}
              {label}
            </span>
            {selectedValue && (
              <Button
                basic
                icon
                size="mini"
                onClick={this.clearFilter}
                aria-label="Clear selection"
                title="Clear selection"
              >
                Clear
              </Button>
            )}
          </Card.Header>
          <Dropdown
            placeholder={placeholder}
            fluid
            search
            selection
            clearable
            loading={loading}
            options={options}
            value={selectedValue}
            onSearchChange={this.handleSearchChange}
            onChange={this.handleChange}
            selectOnBlur={false}
            selectOnNavigation={false}
            noResultsMessage={loading ? "Loading..." : "No results found"}
            style={{ marginTop: "10px" }}
            upward={false}
            // Force high z-index on the dropdown menu
            className="custom-facet-dropdown"
          />
        </Card.Content>
      </Card>
    );
  }
}

DynamicFacet.propTypes = {
  label: PropTypes.string.isRequired,
  apiField: PropTypes.string.isRequired,
  queryField: PropTypes.string.isRequired,
  placeholder: PropTypes.string,
  icon: PropTypes.string,
  maxResults: PropTypes.number,
};

DynamicFacet.defaultProps = {
  placeholder: "Search...",
  icon: null,
  maxResults: 100,
};

export default DynamicFacet;
