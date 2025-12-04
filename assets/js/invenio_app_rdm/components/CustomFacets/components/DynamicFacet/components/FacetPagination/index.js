// Simplified pagination controls - current page with prev/next arrows
import React from "react";
import { Button, Icon } from "semantic-ui-react";
import PropTypes from "prop-types";

const FacetPagination = ({
  currentPage,
  totalPages,
  loading,
  onPageChange,
}) => {
  if (totalPages <= 1) return null;

  return (
    <div
      style={{
        padding: "0.6rem 0.5rem",
        borderTop: "1px solid rgba(34, 36, 38, 0.1)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        gap: "0.75rem",
        backgroundColor: "#fafafa",
      }}
    >
      <Button
        basic
        compact
        size="mini"
        icon
        disabled={currentPage === 1 || loading}
        onClick={() => onPageChange(currentPage - 1)}
        style={{ padding: "0.4rem 0.5rem" }}
        title="Previous page"
      >
        <Icon name="chevron left" />
      </Button>

      <span
        style={{
          fontSize: "0.85rem",
          color: "rgba(0, 0, 0, 0.7)",
          minWidth: "3.5rem",
          textAlign: "center",
        }}
      >
        {currentPage} / {totalPages}
      </span>

      <Button
        basic
        compact
        size="mini"
        icon
        disabled={currentPage === totalPages || loading}
        onClick={() => onPageChange(currentPage + 1)}
        style={{ padding: "0.4rem 0.5rem" }}
        title="Next page"
      >
        <Icon name="chevron right" />
      </Button>
    </div>
  );
};

FacetPagination.propTypes = {
  currentPage: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  loading: PropTypes.bool,
  onPageChange: PropTypes.func.isRequired,
};

FacetPagination.defaultProps = {
  loading: false,
};

export default FacetPagination;
