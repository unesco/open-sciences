/**
 * useDownload
 * Hook that fetches a file via JS, triggers a browser save, and exposes
 * loading / error state plus an auto-dismissing toast (rendered via a React
 * portal). Shared by DownloadMenu and any single-button download triggers.
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { downloadFile } from "../api";

const TOAST_DURATION_MS = 5000;
const DEFAULT_ERROR_MESSAGE =
  "Something went wrong. Please contact administrator if the issue persists.";

const MIME_EXT = {
  "text/csv": "csv",
  "application/json": "json",
  "application/zip": "zip",
  "application/vnd.ms-excel": "xls",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
  "text/plain": "txt",
};

function extensionForBlob(blob) {
  return MIME_EXT[(blob.type || "").split(";")[0].trim()] || "";
}

function triggerBlobDownload(blob, filename, fallbackBaseName) {
  let name = filename;
  if (!name) {
    const ext = extensionForBlob(blob);
    name = ext ? `${fallbackBaseName}.${ext}` : fallbackBaseName;
  }
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

export function useDownload(fallbackBaseName = "download") {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);
  const toastTimer = useRef(null);

  useEffect(() => () => {
    if (abortRef.current) abortRef.current.abort();
    if (toastTimer.current) clearTimeout(toastTimer.current);
  }, []);

  const showErrorToast = useCallback((message) => {
    setError(message);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setError(null), TOAST_DURATION_MS);
  }, []);

  const download = useCallback(async (url) => {
    if (loading) return;
    setLoading(true);
    setError(null);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const { blob, filename } = await downloadFile(url, { signal: controller.signal });
      triggerBlobDownload(blob, filename, fallbackBaseName);
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error("Download failed:", err);
        showErrorToast(DEFAULT_ERROR_MESSAGE);
      }
    } finally {
      abortRef.current = null;
      setLoading(false);
    }
  }, [loading, fallbackBaseName, showErrorToast]);

  const toast = error
    ? createPortal(
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
      )
    : null;

  return { download, loading, toast };
}
