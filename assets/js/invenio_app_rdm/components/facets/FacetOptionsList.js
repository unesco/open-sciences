// Facet options list with checkboxes
import React from "react";
import { List, Checkbox, Label } from "semantic-ui-react";
import PropTypes from "prop-types";

const FacetOptionsList = ({ options, selectedValue, loading, onSelect }) => {
  return (
    <List
      divided
      selection
      verticalAlign="middle"
      style={{
        margin: 0,
        opacity: loading ? 0.6 : 1,
        transition: "opacity 0.2s ease",
      }}
    >
      {options.map((option) => (
        <List.Item
          key={option.key}
          style={{
            padding: "0.6rem 0.8rem",
            cursor: "pointer",
            transition: "background-color 0.1s ease",
          }}
          onClick={() => onSelect(option.value)}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              width: "100%",
            }}
          >
            <Checkbox
              label={
                <label
                  style={{
                    cursor: "pointer",
                    fontSize: "0.92rem",
                    color: "rgba(0, 0, 0, 0.87)",
                  }}
                >
                  {option.text}
                </label>
              }
              checked={selectedValue === option.value}
              onChange={() => onSelect(option.value)}
              style={{ flex: 1, marginRight: "0.5rem" }}
            />
            <Label
              size="mini"
              circular
              style={{
                backgroundColor: "#e0e1e2",
                color: "rgba(0, 0, 0, 0.6)",
                minWidth: "2rem",
                textAlign: "center",
              }}
            >
              {option.count}
            </Label>
          </div>
        </List.Item>
      ))}
    </List>
  );
};

FacetOptionsList.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      text: PropTypes.string.isRequired,
      value: PropTypes.string.isRequired,
      count: PropTypes.number.isRequired,
    })
  ).isRequired,
  selectedValue: PropTypes.string,
  loading: PropTypes.bool,
  onSelect: PropTypes.func.isRequired,
};

FacetOptionsList.defaultProps = {
  selectedValue: null,
  loading: false,
};

export default FacetOptionsList;
