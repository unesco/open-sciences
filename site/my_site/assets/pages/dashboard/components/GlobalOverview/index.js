/**
 * Global Overview Dashboard Component
 * Tab 1: Leaflet world map with participation data
 */

import React, { useState, useEffect, useRef } from "react";
import { loadScript, loadLink } from "../utils";

// ─── Constants ─────────────────────────────────────────────────────────────

const REGIONS = [
  "All regions",
  "Africa",
  "Arab States",
  "Asia-Pacific",
  "Europe",
  "Latin America",
  "North America",
];

const PARTICIPATING_COUNTRIES = [
  "USA","CAN","GBR","FRA","DEU","ITA","ESP","PRT","NLD","BEL","SWE","NOR","DNK","FIN",
  "POL","ROU","GRC","CZE","HUN","SVK","BRA","ARG","MEX","CHL","COL","PER","URY","ECU",
  "BOL","PRY","NGA","KEN","ZAF","ETH","GHA","TZA","UGA","SEN","CMR","CIV","IND","CHN",
  "JPN","KOR","AUS","NZL","IDN","PHL","THA","VNM","MYS","BGD","PAK","LKA","EGY","MAR",
  "TUN","DZA","RUS","UKR","KAZ","UZB","GEO","ARM","AZE",
];

const COUNTRY_COORDS = {
  USA:[38,-97],CAN:[56,-106],GBR:[55,-3],FRA:[46,2],DEU:[51,10],ITA:[42,12],ESP:[40,-4],
  PRT:[39,-8],NLD:[52,5],BEL:[50,4],SWE:[62,15],NOR:[60,8],DNK:[56,10],FIN:[64,26],
  POL:[52,20],ROU:[46,25],GRC:[39,22],CZE:[50,15],HUN:[47,19],SVK:[48,19],
  BRA:[-10,-55],ARG:[-34,-64],MEX:[23,-102],CHL:[-30,-71],COL:[4,-72],PER:[-10,-76],
  URY:[-33,-56],ECU:[-2,-78],BOL:[-17,-65],PRY:[-23,-58],
  NGA:[10,8],KEN:[1,38],ZAF:[-29,25],ETH:[9,40],GHA:[8,-2],TZA:[-6,35],UGA:[1,32],
  SEN:[14,-14],CMR:[6,12],CIV:[7,-5],
  IND:[22,78],CHN:[36,104],JPN:[36,138],KOR:[36,128],AUS:[-27,133],NZL:[-42,174],
  IDN:[-5,120],PHL:[13,122],THA:[15,101],VNM:[16,108],MYS:[4,109],BGD:[24,90],
  PAK:[30,70],LKA:[7,81],EGY:[27,30],MAR:[32,-5],TUN:[34,9],DZA:[28,3],
  RUS:[60,100],UKR:[49,32],KAZ:[48,68],UZB:[41,64],GEO:[42,44],ARM:[40,45],AZE:[40,48],
};

const GLOBAL_FILTERS = [
  {
    id: "understanding",
    label: "Promoting a common understanding of open science, associated benefits, and challenges, as well as diverse paths to open science",
    items: [{ id: "recommendation", label: "UNESCO Recommendation promoted/shared" }],
  },
];

// ─── FilterItem sub-component ──────────────────────────────────────────────

const FilterItem = ({ filter, activeFilters, onToggle }) => {
  const [expanded, setExpanded] = useState(true);
  return (
    <div className="dashboard-filter-group">
      <button
        type="button"
        className="dashboard-filter-group-header"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
      >
        <span className="filter-icon">🔵</span>
        <span className="filter-label">{filter.label}</span>
        <span className="filter-chevron">{expanded ? "▲" : "▼"}</span>
      </button>
      {expanded && (
        <div className="dashboard-filter-items">
          {filter.items.map((item) => (
            <div key={item.id} className="dashboard-filter-item">
              <span className="filter-item-label">{item.label}</span>
              <div className="filter-toggle-group">
                <button
                  type="button"
                  className={`filter-toggle-btn ${activeFilters[item.id] === true ? "active" : ""}`}
                  onClick={() => onToggle(item.id, true)}
                >
                  Yes
                </button>
                <button
                  type="button"
                  className={`filter-toggle-btn ${activeFilters[item.id] === false ? "active" : ""}`}
                  onClick={() => onToggle(item.id, false)}
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

// ─── GlobalOverview component ──────────────────────────────────────────────

export const GlobalOverview = () => {
  const mapRef = useRef(null);
  const leafletMapRef = useRef(null);
  const [activeFilters, setActiveFilters] = useState({ recommendation: true });
  const [region, setRegion] = useState("All regions");
  const activeFilterCount = Object.values(activeFilters).filter(Boolean).length;

  const handleFilterToggle = (id, value) =>
    setActiveFilters((prev) =>
      prev[id] === value
        ? Object.fromEntries(Object.entries(prev).filter(([k]) => k !== id))
        : { ...prev, [id]: value }
    );

  useEffect(() => {
    let mounted = true;
    (async () => {
      loadLink("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css", "leaflet-css");
      await loadScript("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js", "leaflet-js");
      if (!mounted || !mapRef.current || leafletMapRef.current) return;
      const L = window.L;
      const map = L.map(mapRef.current, { zoomControl: true, scrollWheelZoom: false }).setView([20, 10], 2);
      leafletMapRef.current = map;
      L.tileLayer("https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png", {
        attribution: "© OpenStreetMap © CARTO",
        subdomains: "abcd",
        maxZoom: 19,
      }).addTo(map);
      PARTICIPATING_COUNTRIES.forEach((iso) => {
        const coords = COUNTRY_COORDS[iso];
        if (!coords) return;
        L.circleMarker(coords, {
          radius: 6,
          fillColor: "#0073b7",
          color: "#fff",
          weight: 1.5,
          opacity: 1,
          fillOpacity: 0.85,
        })
          .addTo(map)
          .bindTooltip(iso);
      });
    })();
    return () => {
      mounted = false;
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="dash-global">
      <div className="dashboard-subheader">
        <strong>Member States that participated in the survey in year 2025.</strong>
        <div className="dashboard-subheader-actions">
          <button type="button" className="dash-btn primary">
            Search Country Profile 🔍
          </button>
          <button type="button" className="dash-btn outline">
            Download ⬇
          </button>
        </div>
      </div>

      <div className="dashboard-main">
        {/* Filters panel */}
        <div className="dashboard-filters-panel">
          <div className="dashboard-filters-title">FILTERS</div>
          <div className="dashboard-filters-subtitle">
            Select criteria to filter survey responses
          </div>
          <button
            type="button"
            className="dashboard-reset-btn"
            onClick={() => setActiveFilters({})}
          >
            ✕ Reset all filters
          </button>
          <div className="dashboard-filters-list">
            {GLOBAL_FILTERS.map((f) => (
              <FilterItem
                key={f.id}
                filter={f}
                activeFilters={activeFilters}
                onToggle={handleFilterToggle}
              />
            ))}
          </div>
        </div>

        {/* Map panel */}
        <div className="dashboard-map-panel">
          <div className="dashboard-map-topbar">
            <span className="dashboard-filter-selected">
              Filter selected: {activeFilterCount}
            </span>
            <select
              className="dashboard-region-select"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
            >
              {REGIONS.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </div>
          <div className="dashboard-map-legend">
            <span className="legend-item">
              <span className="legend-dot no-data" /> No data
            </span>
            <span className="legend-item">
              <span className="legend-dot participated" /> Participated in the survey (77)
            </span>
            <span className="legend-item">
              <span className="legend-dot matches" /> Matches filters (76)
            </span>
          </div>
          <div ref={mapRef} className="dashboard-leaflet-map" />
        </div>
      </div>
    </div>
  );
};
