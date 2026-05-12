import React, { useEffect, useRef, useCallback, useMemo } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchCountries } from "../../../api";
import {
  WORLD_GEOJSON_URL,
  REGION_LABELS,
  REGION_DISPLAY_TO_API,
  REGION_VIEW,
  ALL_REGIONS,
  normaliseRegion,
  featureStyle,
} from "./constants";

export const MapPanel = ({
  allCountries,
  setAllCountries,
  participatingSet,
  setParticipatingSet,
  matchingSet,
  participatingCount,
  matchingCount,
  filterLoading,
  activeFilterCount,
  region,
  setRegion,
  onCountryClick,
  onNoDataClick,
}) => {
  const mapRef       = useRef(null);
  const leafletRef   = useRef(null);
  const geoLayerRef  = useRef(null);
  const resizeObsRef = useRef(null);

  // Latest-value refs so the once-only map init closure can read fresh state
  const onCountryClickRef   = useRef(onCountryClick);
  const participatingSetRef = useRef(participatingSet);
  const matchingSetRef      = useRef(matchingSet);
  const onNoDataClickRef    = useRef(onNoDataClick);

  useEffect(() => { onCountryClickRef.current = onCountryClick; }, [onCountryClick]);
  useEffect(() => { participatingSetRef.current = participatingSet; }, [participatingSet]);
  useEffect(() => { matchingSetRef.current = matchingSet; }, [matchingSet]);
  useEffect(() => { onNoDataClickRef.current = onNoDataClick; }, [onNoDataClick]);

  // Region → set of ISO3 codes
  const regionIso3Set = useMemo(() => {
    if (region === ALL_REGIONS) return null;
    const apiRegion = normaliseRegion(REGION_DISPLAY_TO_API[region] || region);
    const set = new Set(
      allCountries
        .filter((c) => normaliseRegion(c.region) === apiRegion)
        .map((c) => c.iso_3 || c.iso3 || c.iso_code || "")
        .filter(Boolean)
    );
    return set.size > 0 ? set : null;
  }, [region, allCountries]);

  // Restyle helper
  const applyStyles = useCallback((participating, matching) => {
    if (!geoLayerRef.current) return;
    geoLayerRef.current.setStyle((feature) =>
      featureStyle(feature.id, participating, matching)
    );
  }, []);

  // ── Initial setup: create Leaflet map + load world GeoJSON + countries ──
  useEffect(() => {
    let mounted = true;
    if (!mapRef.current || leafletRef.current) return;

    (async () => {
      try {
        const [geoJson, countriesData] = await Promise.all([
          fetch(WORLD_GEOJSON_URL).then((r) => {
            if (!r.ok) throw new Error(`GeoJSON fetch failed: ${r.status}`);
            return r.json();
          }),
          fetchCountries().catch(() => []),
        ]);
        if (!mounted) return;

        const participating = new Set(
          countriesData.map((c) => c.iso_3 || c.iso3 || c.iso_code || "")
        );
        setParticipatingSet(participating);
        participatingSetRef.current = participating;
        setAllCountries(countriesData);

        const map = L.map(mapRef.current, {
          zoomControl: false,
          scrollWheelZoom: true,
          worldCopyJump: false,
          attributionControl: false,
          minZoom: 1,
          maxBounds: [[-85, -180], [85, 180]],
          maxBoundsViscosity: 1.0,
        }).setView([20, 15], 2);
        leafletRef.current = map;

        L.control.zoom({ position: "bottomleft" }).addTo(map);

        const geoLayer = L.geoJSON(geoJson, {
          style: (feature) => featureStyle(feature.id, participating, matchingSetRef.current),
          onEachFeature: (feature, layer) => {
            const name = feature.properties?.name || feature.id;
            const iso3 = feature.id;
            layer.bindTooltip(name, { sticky: true, className: "map-tooltip" });

            layer.on({
              mouseover: (e) => {
                e.target.setStyle({ weight: 1.6, color: "#1a6fa8" });
                e.target.bringToFront();
              },
              mouseout: (e) => {
                e.target.setStyle(
                  featureStyle(
                    e.target.feature.id,
                    participatingSetRef.current,
                    matchingSetRef.current
                  )
                );
              },
              click: () => {
                if (
                  onCountryClickRef.current &&
                  iso3 &&
                  participatingSetRef.current.has(iso3)
                ) {
                  onCountryClickRef.current(iso3, name);
                } else if (
                  matchingSetRef.current !== null &&
                  !participatingSetRef.current.has(iso3)
                ) {
                  onNoDataClickRef.current && onNoDataClickRef.current();
                }
              },
            });
          },
        }).addTo(map);
        geoLayerRef.current = geoLayer;

        if (typeof ResizeObserver !== "undefined") {
          const ro = new ResizeObserver(() => {
            if (leafletRef.current) leafletRef.current.invalidateSize();
          });
          ro.observe(mapRef.current);
          resizeObsRef.current = ro;
        }
        requestAnimationFrame(() => {
          if (mounted && leafletRef.current) leafletRef.current.invalidateSize();
        });
      } catch (err) {
        console.error("[MapPanel] Map init failed:", err);
      }
    })();

    return () => {
      mounted = false;
      if (resizeObsRef.current) {
        resizeObsRef.current.disconnect();
        resizeObsRef.current = null;
      }
      if (leafletRef.current) {
        leafletRef.current.remove();
        leafletRef.current = null;
        geoLayerRef.current = null;
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Restyle on matchingSet or participatingSet change
  useEffect(() => {
    applyStyles(participatingSet, matchingSet);
  }, [matchingSet, participatingSet, applyStyles]);

  // Zoom when region changes
  useEffect(() => {
    const map = leafletRef.current;
    if (!map) return;

    if (region === ALL_REGIONS) {
      map.flyTo([20, 15], 2, { duration: 0.6 });
      return;
    }

    const view = REGION_VIEW[region];
    if (view) {
      map.flyTo(view.center, view.zoom, { duration: 0.6 });
    }
  }, [region]);

  // Country list
  const displayedCountries = (() => {
    let list = allCountries;
    if (matchingSet !== null) {
      list = list.filter((c) => matchingSet.has(c.iso_3 || c.iso3 || c.iso_code || ""));
    }
    return list.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
  })();

  return (
    <div className="dashboard-map-panel">
      <div className="dashboard-map-topbar">
        <span className="dashboard-filter-selected">
          Filter selected: {activeFilterCount}
          {filterLoading && <span className="map-filter-spinner"> \u27F3</span>}
        </span>
        <select
          className="dashboard-region-select"
          value={region}
          onChange={(e) => setRegion(e.target.value)}
        >
          {REGION_LABELS.map((r) => (
            <option key={r}>{r}</option>
          ))}
        </select>
      </div>

      <div className="dashboard-map-legend">
        <span className="legend-item">
          <span className="legend-dot no-data" /> No data
        </span>
        {matchingSet !== null && (
          <>
            <span className="legend-item">
              <span className="legend-dot participated" />{" "}
              Participated in the survey ({participatingCount})
            </span>
            <span className="legend-item">
              <span className="legend-dot matches" />{" "}
              Matches filters ({matchingCount})
            </span>
          </>
        )}
      </div>

      <div ref={mapRef} className="dashboard-leaflet-map" />

      {matchingSet !== null && displayedCountries.length > 0 && (
        <div className="dashboard-map-country-list">
          {displayedCountries.map((c) => {
            const iso3 = c.iso_3 || c.iso3 || c.iso_code;
            return (
              <button
                key={iso3 || c.name}
                type="button"
                className="map-country-link"
                onClick={() => {
                  if (onCountryClick && iso3) onCountryClick(iso3, c.name);
                }}
              >
                {c.name}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
