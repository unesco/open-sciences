// Facet header component with title
import React from "react";
import { Card } from "semantic-ui-react";
import PropTypes from "prop-types";

const FacetHeader = ({ label }) => {
  return (
    <Card.Header
      as="h2"
      style={{
        color: "#212121",
        display: "flex",
        alignItems: "center",
        justifyContent: "flex-start",
        marginBottom: "0.75rem",
        fontSize: "0.92rem",
        fontWeight: 600,
      }}
    >
      {label}
    </Card.Header>
  );
};

FacetHeader.propTypes = {
  label: PropTypes.string.isRequired,
};

export default FacetHeader;
