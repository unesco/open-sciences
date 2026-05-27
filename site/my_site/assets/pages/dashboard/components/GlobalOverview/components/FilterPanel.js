import React, { useState } from "react";

import { InfoIcon } from "../../InfoIcon";

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
          <img src="/static/images/menu_icon.png" alt="Section icon" className="topic-medal-icon" />
        </span>
        <span className="filter-label">{filter.label}</span>
        <span className="filter-chevron">{expanded ? "\u25B2" : "\u25BC"}</span>
      </button>
      {expanded && (
        <div className="dashboard-filter-items">
          {filter.items.map((item) => {
            const labelParts = (item.label || "").split(" ");
            const lastWord = labelParts.pop() || "";
            const leading = labelParts.join(" ");
            return (
              <div key={item.id} className="dashboard-filter-item">
                <span className="filter-item-label">
                  {leading && `${leading} `}
                  <span className="filter-item-label-tail">
                    {lastWord}
                    <InfoIcon
                      description={item.description}
                      options={item.options}
                      modalTitle={item.label}
                    />
                  </span>
                </span>
                <div className="filter-toggle-group">
                  {(item.options || []).map((opt) => (
                    <button
                      key={opt.code}
                      type="button"
                      className={`filter-toggle-btn${activeFilters[item.id] === opt.code ? " active" : ""}`}
                      onClick={() => onToggle(item.id, opt.code)}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
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
        <div className="dashboard-filters-empty">Loading filters..</div>
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
