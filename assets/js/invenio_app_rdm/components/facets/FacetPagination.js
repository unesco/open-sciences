// Pagination controls for facet options
import React from "react";
import { Button, Icon } from "semantic-ui-react";
import PropTypes from "prop-types";

const FacetPagination = ({
  currentPage,
  totalPages,
  loading,
  onPageChange,
}) => {
  // Generate page numbers with ellipsis for smart pagination
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5;

    if (totalPages <= maxPagesToShow) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      const halfRange = Math.floor(maxPagesToShow / 2);
      let start = Math.max(1, currentPage - halfRange);
      let end = Math.min(totalPages, start + maxPagesToShow - 1);

      if (end - start < maxPagesToShow - 1) {
        start = Math.max(1, end - maxPagesToShow + 1);
      }

      if (start > 1) {
        pages.push(1);
        if (start > 2) pages.push("...");
      }

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (end < totalPages) {
        if (end < totalPages - 1) pages.push("...");
        pages.push(totalPages);
      }
    }

    return pages;
  };

  if (totalPages <= 1) return null;

  return (
    <div
      style={{
        padding: "0.75rem 0.5rem",
        borderTop: "1px solid rgba(34, 36, 38, 0.1)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
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
        style={{ padding: "0.5rem" }}
      >
        <Icon name="chevron left" />
      </Button>

      <div
        style={{
          display: "flex",
          gap: "0.25rem",
          alignItems: "center",
        }}
      >
        {getPageNumbers().map((page, idx) =>
          page === "..." ? (
            <span
              key={`ellipsis-${idx}`}
              style={{ padding: "0 0.25rem", color: "#999" }}
            >
              ...
            </span>
          ) : (
            <Button
              key={page}
              basic={currentPage !== page}
              primary={currentPage === page}
              compact
              size="mini"
              disabled={loading}
              onClick={() => onPageChange(page)}
              style={{
                minWidth: "2rem",
                padding: "0.4rem 0.5rem",
                fontSize: "0.8rem",
              }}
            >
              {page}
            </Button>
          )
        )}
      </div>

      <Button
        basic
        compact
        size="mini"
        icon
        disabled={currentPage === totalPages || loading}
        onClick={() => onPageChange(currentPage + 1)}
        style={{ padding: "0.5rem" }}
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
