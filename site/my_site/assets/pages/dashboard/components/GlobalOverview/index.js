/**
 * Global Overview Dashboard Component
 * Tab 1: Leaflet choropleth world map with survey participation & filter data
 */

import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  fetchMultiFilter,
  fetchSurveySections,
  fetchSurveyQuestions,
} from "../../api";
import { FilterPanel } from "./components/FilterPanel";
import { MapPanel } from "./components/MapPanel";
import { NoDataModal } from "./components/NoDataModal";
import { CountriesModal } from "./components/CountriesModal";
import { buildFilterTree, ALL_REGIONS } from "./components/constants";

export const GlobalOverview = ({ onCountryClick }) => {
  const [allCountries, setAllCountries]         = useState([]);
  const [participatingSet, setParticipatingSet] = useState(new Set());
  const [matchingSet, setMatchingSet]           = useState(null);
  const [filterLoading, setFilterLoading]       = useState(false);
  const [activeFilters, setActiveFilters]       = useState({});
  const [region, setRegion]                     = useState(ALL_REGIONS);
  const [globalFilters, setGlobalFilters]       = useState([]);
  const [showNoDataModal, setShowNoDataModal]   = useState(false);
  const [showCountriesModal, setShowCountriesModal] = useState(false);

  // Derived counts
  const participatingCount = participatingSet.size;
  const matchingCount      = matchingSet !== null ? matchingSet.size : participatingCount;
  const activeFilterCount  = Object.keys(activeFilters).length;

  // Load section/question metadata from CMS
  useEffect(() => {
    let mounted = true;
    Promise.all([fetchSurveySections(), fetchSurveyQuestions()])
      .then(([sections, questions]) => {
        if (!mounted) return;
        const tree = buildFilterTree(sections, questions);
        setGlobalFilters(tree);
        if (tree.length > 0 && tree[0].items.length > 0) {
          setActiveFilters({ [tree[0].items[0].id]: "Y" });
        }
      })
      .catch((err) => console.error("[GlobalOverview] filter metadata load failed:", err));
    return () => { mounted = false; };
  }, []);

  // Toggle a filter item (same value again = deselect)
  const handleFilterToggle = useCallback((id, value) => {
    setActiveFilters((prev) =>
      prev[id] === value
        ? Object.fromEntries(Object.entries(prev).filter(([k]) => k !== id))
        : { ...prev, [id]: value }
    );
  }, []);

  // Re-query multi-filter API when activeFilters change
  useEffect(() => {
    const qLookup = {};
    globalFilters.forEach((g) =>
      g.items.forEach((it) => { qLookup[it.id] = it.question; })
    );

    const filtersArray = Object.entries(activeFilters)
      .filter(([, val]) => val)
      .map(([id, val]) => ({ question: qLookup[id], answers: [val] }))
      .filter((f) => f.question);

    if (filtersArray.length === 0) {
      setMatchingSet(null);
      return;
    }

    setFilterLoading(true);
    fetchMultiFilter(filtersArray)
      .then((data) => setMatchingSet(new Set((data.countries || []).map((c) => c.iso3))))
      .catch(() => setMatchingSet(null))
      .finally(() => setFilterLoading(false));
  }, [activeFilters, globalFilters]);

  return (
    <div className="dash-global">
      {showNoDataModal && <NoDataModal onClose={() => setShowNoDataModal(false)} />}
      {showCountriesModal && (
        <CountriesModal
          onClose={() => setShowCountriesModal(false)}
          onCountryClick={onCountryClick}
        />
      )}

      <div className="dashboard-subheader">
        <strong>Member States that participated in the survey in year 2025.</strong>
        <div className="dashboard-subheader-actions">
          <button type="button" className="dash-btn primary" onClick={() => setShowCountriesModal(true)}>
            Search Country Profile
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
          </button>
          <button type="button" className="dash-btn outline">
            Download
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
          </button>
        </div>
      </div>

      <div className="dashboard-main">
        <FilterPanel
          globalFilters={globalFilters}
          activeFilters={activeFilters}
          activeFilterCount={activeFilterCount}
          onToggle={handleFilterToggle}
          onReset={() => setActiveFilters({})}
        />

        <MapPanel
          allCountries={allCountries}
          setAllCountries={setAllCountries}
          participatingSet={participatingSet}
          setParticipatingSet={setParticipatingSet}
          matchingSet={matchingSet}
          participatingCount={participatingCount}
          matchingCount={matchingCount}
          filterLoading={filterLoading}
          activeFilterCount={activeFilterCount}
          region={region}
          setRegion={setRegion}
          onCountryClick={onCountryClick}
          onNoDataClick={() => setShowNoDataModal(true)}
        />
      </div>
    </div>
  );
};
