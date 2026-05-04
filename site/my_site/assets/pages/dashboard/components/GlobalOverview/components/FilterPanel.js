import React, { useState } from "react";
import { MedalIcon } from "../../utils";

const FilterGroup = ({ filter, activeFilters, onToggle, defaultExpanded = false }) => {
  const [expanded, setExpanded] = useState(defaultExpanded);
  return (
    <div className="dashboard-filter-group">
      <button
        type="button"
        className="dashboard-filter-group-header"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
      >
        <span className="filter-icon">
          <MedalIcon />
        </span>
        <span className="filter-label">{filter.label}</span>
        <span className="filter-chevron">{expanded ? "\u25B2" : "\u25BC"}</span>
      </button>
      {expanded && (
        <div className="dashboard-filter-items">
          {filter.items.map((item) => (
              <div key={item.id} className="dashboard-filter-item">
                <span className="filter-item-label">
                  {item.label}
                </span>
                <div className="filter-toggle-group">
                  <button
                    type="button"
                    className={`filter-toggle-btn${activeFilters[item.id] === "Y" ? " active" : ""}`}
                    onClick={() => onToggle(item.id, "Y")}
                  >
                    Yes
                  </button>
                  <button
                    type="button"
                    className={`filter-toggle-btn${activeFilters[item.id] === "N" ? " active" : ""}`}
                    onClick={() => onToggle(item.id, "N")}
                  >
                    No
                  </button>
                </div>
              </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const FilterPanel = ({
  globalFilters,
  activeFilters,
  activeFilterCount,
  onToggle,
  onReset,
}) => (
  <div className="dashboard-filters-panel">
    <div className="dashboard-filters-title">FILTERS</div>
    <div className="dashboard-filters-subtitle">
      Select criteria to filter survey responses
    </div>
    {activeFilterCount > 0 && (
      <button type="button" className="dashboard-reset-btn" onClick={onReset}>
        &times; Reset all filters
      </button>
    )}
    <div className="dashboard-filters-list">
      {globalFilters.length === 0 ? (
        <div className="dashboard-filters-empty">Loading filters\u2026</div>
      ) : (
        globalFilters.map((f, idx) => (
          <FilterGroup
            key={f.id}
            filter={f}
            activeFilters={activeFilters}
            onToggle={onToggle}
            defaultExpanded={idx === 0}
          />
        ))
      )}
    </div>
  </div>
);
