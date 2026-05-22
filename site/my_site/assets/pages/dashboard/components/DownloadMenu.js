/**
 * DownloadMenu
 * Outline "Download" button that opens a small popup with two options:
 *  - Download filtered data  → uses `filteredHref`
 *  - Download all data       → uses `allHref`
 *
 * Each option fetches the file via JS so we can show a spinner on the trigger
 * button while the server prepares the response, then triggers a download via
 * a temporary blob URL. The "filtered" option is hidden when `filteredHref` is
 * falsy.
 */

import React, { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import PropTypes from "prop-types";
import { downloadFile } from "../api";

const TOAST_DURATION_MS = 5000;
const DEFAULT_ERROR_MESSAGE =
  "Something went wrong. Please contact administrator if the issue persists.";

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

const MIME_EXT = {
  "text/csv": "csv",
  "application/json": "json",
  "application/zip": "zip",
  "application/vnd.ms-excel": "xls",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
  "text/plain": "txt",
};

// Filename used when the server omits Content-Disposition. Extension is
// inferred from the blob's mime type so e.g. CSV → survey_responses.csv.
function buildFallbackName(blob) {
  const ext = MIME_EXT[(blob.type || "").split(";")[0].trim()] || "";
  return ext ? `survey_responses.${ext}` : "survey_responses";
}

function triggerBlobDownload(blob, filename) {
  const name = filename || buildFallbackName(blob);
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.rel = "noopener";
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(objectUrl);
}

export const DownloadMenu = ({ filteredHref, allHref }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const wrapRef = useRef(null);
  const abortRef = useRef(null);
  const toastTimer = useRef(null);

  const showErrorToast = (message) => {
    setError(message);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setError(null), TOAST_DURATION_MS);
  };

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

  // Abort any in-flight fetch and clear the toast timer on unmount
  useEffect(() => () => {
    if (abortRef.current) abortRef.current.abort();
    if (toastTimer.current) clearTimeout(toastTimer.current);
  }, []);

  const handleDownload = async (url) => {
    if (loading) return;
    setOpen(false);
    setLoading(true);
    setError(null);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const { blob, filename } = await downloadFile(url, { signal: controller.signal });
      triggerBlobDownload(blob, filename);
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error("Download failed:", err);
        showErrorToast(DEFAULT_ERROR_MESSAGE);
      }
    } finally {
      abortRef.current = null;
      setLoading(false);
    }
  };

  return (
    <div className="download-menu" ref={wrapRef}>
      <button
        type="button"
        className="dash-btn outline"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-busy={loading}
        disabled={loading}
        onClick={() => setOpen((v) => !v)}
      >
        {loading ? "Downloading…" : "Download"}
        {loading ? <Spinner /> : <DownloadIcon />}
      </button>

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

      {error && createPortal(
        <div className="download-toast" role="alert">
          <span>{error}</span>
          <button
            type="button"
            className="download-toast-close"
            aria-label="Dismiss"
            onClick={() => setError(null)}
          >
            ×
          </button>
        </div>,
        document.body,
      )}
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
