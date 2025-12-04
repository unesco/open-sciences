// Facet header component with title and icon
import React from "react";
import { Card, Icon } from "semantic-ui-react";
import PropTypes from "prop-types";

const FacetHeader = ({ label, icon }) => {
  return (
    <Card.Header
      as="h2"
      style={{
        color: "#2185d0",
        display: "flex",
        alignItems: "center",
        marginBottom: "0.75rem",
        fontSize: "0.92rem",
        fontWeight: 600,
      }}
    >
      {icon && (
        <Icon name={icon} style={{ marginRight: "8px", color: "#2185d0" }} />
      )}
      {label}
    </Card.Header>
  );
};

FacetHeader.propTypes = {
  label: PropTypes.string.isRequired,
  icon: PropTypes.string,
};

FacetHeader.defaultProps = {
  icon: null,
};

export default FacetHeader;
