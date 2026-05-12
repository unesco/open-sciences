/**
 * Challenges Dashboard Component
 * Tab 3: Word cloud of most frequently mentioned Open Science challenges
 */

import React, { useState, useEffect, useMemo } from "react";
import { fetchCountries, fetchWordcloud } from "../../api";
import { REGION_LABELS, ALL_REGIONS, regionToApi } from "../GlobalOverview/components/constants";
import { WordCloud } from "./components/WordCloud";
import { TermDetail } from "./components/TermDetail";
import { termsToWords } from "./utils";

// ─── Challenges component ──────────────────────────────────────────────────

export const Challenges = ({ onCountryClick }) => {
  const [region, setRegion] = useState(ALL_REGIONS);
  const [terms, setTerms] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedTerm, setSelectedTerm] = useState(null);
  const [countryMap, setCountryMap] = useState({});

  // Fetch countries once on mount for ISO3 → name mapping
  useEffect(() => {
    fetchCountries()
      .then((list) => {
        const map = {};
        (list || []).forEach((c) => {
          const iso = c.iso_3 || c.iso3 || c.iso_code || "";
          if (iso) map[iso.toUpperCase()] = c.name || iso;
        });
        setCountryMap(map);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const apiRegion = region !== ALL_REGIONS ? regionToApi(region) : null;
    fetchWordcloud({ region: apiRegion })
      .then((data) => setTerms(data.terms || []))
      .catch(() => setTerms([]));
  }, [region]);

  const words = useMemo(() => termsToWords(terms), [terms]);

  // Sorted by count descending for the listing
  const sortedWords = useMemo(
    () => [...words].sort((a, b) => b.count - a.count),
    [words]
  );

  const filteredWords = useMemo(() => {
    if (!search.trim()) return sortedWords;
    const q = search.trim().toLowerCase();
    return sortedWords.filter((w) => w.text.toLowerCase().includes(q));
  }, [sortedWords, search]);

  const handleTermClick = (word) => {
    // Find the original API term (lowercase) for the API call
    const original = terms.find(
      (t) => t.term.toLowerCase() === word.text.toLowerCase()
    );
    setSelectedTerm({
      term: original ? original.term : word.text,
      count: word.count,
    });
  };

  // Detail view
  if (selectedTerm) {
    return (
      <div className="dash-challenges">
        <TermDetail
          term={selectedTerm.term}
          count={selectedTerm.count}
          region={region !== ALL_REGIONS ? regionToApi(region) : null}
          countryMap={countryMap}
          onBack={() => setSelectedTerm(null)}
          onCountryClick={onCountryClick}
        />
      </div>
    );
  }

  return (
    <div className="dash-challenges">
      <div className="dashboard-subheader">
        <strong>
          Most frequently mentioned challenges and concerns in the implementation of open science.
        </strong>
        <div className="dashboard-subheader-actions">
          <select
            className="dashboard-region-select"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          >
            {REGION_LABELS.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
          <button type="button" className="dash-btn outline">
            Download
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
          </button>
        </div>
      </div>

      <WordCloud words={words} onWordClick={handleTermClick} />

      <div className="challenge-search-section">
        <div className="challenge-search-bar">
          <input
            type="text"
            className="challenge-search-input"
            placeholder="Search by challenge"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="button" className="dash-btn primary challenge-search-btn">
            Search
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
          </button>
        </div>
        <div className="challenge-list">
          {filteredWords.map((w) => (
            <button
              key={w.text}
              type="button"
              className="challenge-list-link"
              onClick={() => handleTermClick(w)}
            >
              {w.text} ({w.count})
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
