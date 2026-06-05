/**
 * CmsPage
 * Renders a single CMS page ({ title, body }) selected by the URL hash slug,
 * e.g. /page#about fetches /cms/api/pages/about.
 */

import React, { useEffect, useState } from "react";

/** Read the slug from the URL hash ("#about" -> "about"). */
const slugFromHash = () =>
  decodeURIComponent((window.location.hash || "").replace(/^#/, "")).trim();

/**
 * Fetch a CMS page via the shared global CmsApi helper (static/js/cms-api.js),
 * loaded by the page template. Centralizes host/lang handling for all CMS calls.
 */
const fetchCmsPage = (slug) => {
  if (!window.CmsApi || typeof window.CmsApi.fetchPage !== "function") {
    return Promise.reject(new Error("CmsApi helper not loaded"));
  }
  return window.CmsApi.fetchPage(slug);
};

const HTMLBlock = ({ html }) => {
  if (!html) return null;
  // Body HTML is sanitized server-side by the Drupal renderer pipeline.
  return <div className="cms-page-body" dangerouslySetInnerHTML={{ __html: html }} />;
};

export const CmsPage = () => {
  const [slug, setSlug] = useState(slugFromHash());
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | notfound | error

  // Re-render when the hash changes (e.g. navigating between CMS pages).
  useEffect(() => {
    const onHashChange = () => setSlug(slugFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    if (!slug) {
      setStatus("notfound");
      return;
    }
    let cancelled = false;
    setStatus("loading");
    fetchCmsPage(slug)
      .then((page) => {
        if (cancelled) return;
        setData(page);
        setStatus("ready");
        if (page && page.title) document.title = page.title;
      })
      .catch((err) => {
        if (cancelled) return;
        setStatus(err.status === 404 ? "notfound" : "error");
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (status === "loading") {
    return (
      <div className="cms-page">
        <div className="cms-page-header">
          <div className="cms-page-title skeleton">&nbsp;</div>
        </div>
        <p className="cms-page-body skeleton">&nbsp;</p>
      </div>
    );
  }

  if (status === "notfound") {
    return (
      <div className="cms-page">
        <h1 className="cms-page-title">Page not found</h1>
        <p>The page you are looking for is not available.</p>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="cms-page">
        <h1 className="cms-page-title">Something went wrong</h1>
        <p>Could not load this page at the moment. Please try again later.</p>
      </div>
    );
  }

  return (
    <div className="cms-page">
      <div className="cms-page-header">
        <h1 className="cms-page-title">{data.title}</h1>
      </div>
      <HTMLBlock html={data.body} />
    </div>
  );
};
