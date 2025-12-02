// Facet header component with title, icon, and clear button
import React from "react";
import { Card, Icon, Button } from "semantic-ui-react";
import PropTypes from "prop-types";

const FacetHeader = ({ label, icon, selectedValue, onClear }) => {
  return (
    <Card.Header
      as="h2"
      style={{
        color: "#2185d0",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: "0.75rem",
        fontSize: "0.92rem",
        fontWeight: 600,
      }}
    >
      <span style={{ display: "flex", alignItems: "center" }}>
        {icon && (
          <Icon name={icon} style={{ marginRight: "8px", color: "#2185d0" }} />
        )}
        {label}
      </span>
      {selectedValue && (
        <Button
          basic
          compact
          size="mini"
          onClick={onClear}
          aria-label="Clear selection"
          title="Clear selection"
          style={{
            padding: "0.35rem 0.5rem",
            fontSize: "0.7rem",
            marginLeft: "0.5rem",
          }}
        >
          <Icon name="close" style={{ margin: 0, fontSize: "0.9rem" }} />
        </Button>
      )}
    </Card.Header>
  );
};

FacetHeader.propTypes = {
  label: PropTypes.string.isRequired,
  icon: PropTypes.string,
  selectedValue: PropTypes.string,
  onClear: PropTypes.func.isRequired,
};

FacetHeader.defaultProps = {
  icon: null,
  selectedValue: null,
};

export default FacetHeader;
