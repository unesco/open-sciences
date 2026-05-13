/**
 * TermDetail Component
 * Shows a paginated table of country + context snippets for a selected term.
 */

import React, { useState, useEffect, useMemo } from "react";
import { fetchTermContext } from "../../../api";

const PAGE_SIZES = [20, 50, 100];

export const TermDetail = ({ term, count, region, countryMap, onBack, onCountryClick }) => {
  const [contexts, setContexts] = useState([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sortDir, setSortDir] = useState("asc");

  // Fetch term contexts
  useEffect(() => {
    fetchTermContext(term, { region: region || undefined })
      .then((data) => {
        setContexts(data.contexts || []);
        setPage(1);
      })
      .catch(() => setContexts([]));
  }, [term, region]);

  const countries = countryMap || {};

  const sortedContexts = useMemo(() => {
    const sorted = [...contexts].sort((a, b) => {
      const nameA = (countries[a.country] || a.country).toLowerCase();
      const nameB = (countries[b.country] || b.country).toLowerCase();
      return nameA.localeCompare(nameB);
    });
    return sortDir === "desc" ? sorted.reverse() : sorted;
  }, [contexts, countries, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sortedContexts.length / pageSize));
  const pagedContexts = sortedContexts.slice(
    (page - 1) * pageSize,
    page * pageSize
  );

  const toggleSort = () => setSortDir((d) => (d === "asc" ? "desc" : "asc"));

  // Pagination helpers
  const goFirst = () => setPage(1);
  const goPrev = () => setPage((p) => Math.max(1, p - 1));
  const goNext = () => setPage((p) => Math.min(totalPages, p + 1));
  const goLast = () => setPage(totalPages);

  // Show up to 5 page numbers around current
  const pageNumbers = useMemo(() => {
    const pages = [];
    let start = Math.max(1, page - 2);
    let end = Math.min(totalPages, start + 4);
    start = Math.max(1, end - 4);
    for (let i = start; i <= end; i++) pages.push(i);
    if (end < totalPages) pages.push(totalPages);
    return pages;
  }, [page, totalPages]);

  const displayTerm = term.charAt(0).toUpperCase() + term.slice(1);

  return (
    <div className="term-detail">
      <button type="button" className="term-detail-back" onClick={onBack}>
        &larr; Go back to word Cloud
      </button>

      <h2 className="term-detail-title">
        {displayTerm} ({count})
      </h2>

      <table className="term-detail-table">
        <thead>
          <tr>
            <th className="term-detail-th-country" onClick={toggleSort}>
              Country {sortDir === "asc" ? "↑" : "↓"}
            </th>
            <th>Context</th>
          </tr>
        </thead>
        <tbody>
          {pagedContexts.map((ctx, i) => {
            const countryName = countries[ctx.country] || ctx.country;
            return (
              <tr key={`${ctx.country}-${i}`}>
                <td className="term-detail-country">
                  <button
                    type="button"
                    className="term-detail-country-link"
                    onClick={() => onCountryClick(ctx.country, countryName)}
                    title="See country profile"
                  >
                    {countryName}
                  </button>
                </td>
                <td
                  className="term-detail-snippet"
                  dangerouslySetInnerHTML={{ __html: ctx.snippet }}
                />
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Pagination */}
      <div className="term-detail-pagination">
        <div className="term-detail-pagination-nav">
          <button type="button" disabled={page === 1} onClick={goFirst}>
            &laquo; First
          </button>
          <button type="button" disabled={page === 1} onClick={goPrev}>
            &lsaquo; Back
          </button>
          {pageNumbers.map((p) => (
            <button
              key={p}
              type="button"
              className={p === page ? "active" : ""}
              onClick={() => setPage(p)}
            >
              {p}
            </button>
          ))}
          <button type="button" disabled={page === totalPages} onClick={goNext}>
            Next &rsaquo;
          </button>
          <button type="button" disabled={page === totalPages} onClick={goLast}>
            Last &raquo;
          </button>
        </div>
        <div className="term-detail-pagination-size">
          Items per page
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
          >
            {PAGE_SIZES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};
