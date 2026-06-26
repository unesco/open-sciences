/**
 * DownloadMenu
 * Outline "Download" button that opens a small popup with two options:
 *  - Download filtered data  → uses `filteredHref`
 *  - Download all data       → uses `allHref`
 *
 * The actual fetch + toast is handled by the shared `useDownload` hook.
 * The "filtered" option is hidden when `filteredHref` is falsy.
 */

import React, { useState, useRef, useEffect } from "react";
import PropTypes from "prop-types";
import { useDownload } from "./useDownload";
import { ComingSoonWrap } from "./ComingSoonWrap";
import { DOWNLOAD_COMING_SOON } from "../constants";

const DownloadIcon = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

const Spinner = () => (
  <svg
    className="download-spinner"
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
  >
    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
  </svg>
);

export const DownloadMenu = ({ filteredHref, allHref }) => {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);
  const { download, loading, toast } = useDownload("survey_responses");

  useEffect(() => {
    if (!open) return undefined;
    const onDocClick = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const handleDownload = (url) => {
    setOpen(false);
    download(url);
  };

  return (
    <div className="download-menu" ref={wrapRef}>
      <ComingSoonWrap>
        <button
          type="button"
          className="dash-btn outline"
          aria-haspopup="menu"
          aria-expanded={open}
          aria-busy={loading}
          disabled={loading}
          // While downloads are disabled the button only surfaces the
          // "Coming soon" tooltip on hover — it doesn't open the popup.
          onClick={DOWNLOAD_COMING_SOON ? undefined : () => setOpen((v) => !v)}
        >
          {loading ? "Downloading…" : "Download"}
          {loading ? <Spinner /> : <DownloadIcon />}
        </button>
      </ComingSoonWrap>

      {open && !loading && (
        <div className="download-menu-popup" role="menu">
          {filteredHref && (
            <button
              type="button"
              className="download-menu-item"
              role="menuitem"
              onClick={() => handleDownload(filteredHref)}
            >
              <DownloadIcon />
              <span>Download filtered data</span>
            </button>
          )}
          <button
            type="button"
            className="download-menu-item"
            role="menuitem"
            onClick={() => handleDownload(allHref)}
          >
            <DownloadIcon />
            <span>Download all data</span>
          </button>
        </div>
      )}

      {toast}
    </div>
  );
};

DownloadMenu.propTypes = {
  filteredHref: PropTypes.string,
  allHref: PropTypes.string.isRequired,
};

DownloadMenu.defaultProps = {
  filteredHref: "",
};
