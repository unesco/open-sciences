/**
 * PlsDetail
 * Renders a single Plain Language Summary, with hero, body sections,
 * sidebar (publication / authors / SDGs / tags) and related cards.
 */

import React, { useEffect, useState, useMemo } from "react";
import PropTypes from "prop-types";
import { useParams } from "react-router-dom";
import { fetchPlsDetail, resolveCmsAsset } from "./api";

const ArrowIcon = ({ className }) => (
  <svg className={className} width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
    <path
      fill="currentColor"
      d="M12 4L10.59 5.41L16.17 11H4V13H16.17L10.59 18.59L12 20L20 12L12 4Z"
    />
  </svg>
);

const InfoIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
    <circle cx="12" cy="12" r="9.25" fill="none" stroke="currentColor" strokeWidth="1.5" />
    <circle cx="12" cy="7.8" r="1.15" fill="currentColor" />
    <rect x="11.1" y="10.6" width="1.8" height="6.4" rx="0.9" fill="currentColor" />
  </svg>
);


const HTMLBlock = ({ html }) => {
  if (!html) return null;
  // The Drupal renderer pipeline (renderInIsolation with a text format)
  // already sanitizes HTML server-side, so we render it as-is.
  return (
    <div className="pls-html" dangerouslySetInnerHTML={{ __html: html }} />
  );
};
HTMLBlock.propTypes = { html: PropTypes.string };

const SECTION_DEFS = [
  { key: "what_was_done", anchor: "what-was-done", title: "What did the researchers do and find?" },
  { key: "why_was_done", anchor: "why-was-done", title: "Why was this study done, and why is it important?" },
  { key: "meaning", anchor: "meaning", title: "What do these findings mean?" },
];

const smoothScrollToAnchor = (e, anchor) => {
  e.preventDefault();
  const el = document.getElementById(anchor);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    // Update the URL hash without jumping
    if (window.history.replaceState) {
      window.history.replaceState(null, "", `#${anchor}`);
    }
  }
};

export const PlsDetail = () => {
  const { nid } = useParams();
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ok | notfound | error
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    fetchPlsDetail(nid)
      .then((d) => {
        if (cancelled) return;
        setData(d);
        setStatus("ok");
      })
      .catch((e) => {
        if (cancelled) return;
        if (e.status === 404) {
          setStatus("notfound");
        } else {
          setError(e);
          setStatus("error");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [nid]);

  const sections = useMemo(() => {
    if (!data) return [];
    return SECTION_DEFS.filter((s) => data[s.key]);
  }, [data]);

  // Summary nav = body sections + the related section (when present).
  const summaryItems = useMemo(() => {
    const items = sections.map((s) => ({ anchor: s.anchor, title: s.title }));
    if (data?.related?.length) {
      items.push({ anchor: "related", title: "You may be interested to read" });
    }
    return items;
  }, [sections, data]);

  const scrollToTop = () =>
    window.scrollTo({ top: 0, behavior: "smooth" });

  if (status === "loading") {
    return (
      <div className="pls-page pls-state">
        <div className="pls-spinner" aria-label="Loading" />
      </div>
    );
  }
  if (status === "notfound") {
    return (
      <div className="pls-page pls-state">
        <h1>Plain Language Summary not found</h1>
        <a href="/" className="pls-link">Back to home</a>
      </div>
    );
  }
  if (status === "error") {
    return (
      <div className="pls-page pls-state">
        <h1>Could not load this summary</h1>
        <p>{error?.message || "Unknown error"}</p>
      </div>
    );
  }

  const pub = data.original_publication || {};
  const tags = data.tags || [];
  const sdgs = data.sdgs || [];
  const related = data.related || [];
  const authors = pub.authors || [];
  const sponsorLogo = resolveCmsAsset(pub.sponsor_logo);
  const heroImage =
    resolveCmsAsset(data.field_hero_image) || "/static/images/placeholderimg.jpg";
  const heroCopyright = data.field_hero_copyright || "";

  return (
    <div className="pls-page">
      {/* Hero */}
      <section
        className="pls-hero"
        style={{ backgroundImage: `url('${heroImage}')` }}
      >
        <div className="pls-hero-inner">
          <p className="pls-hero-eyebrow">
            Summary descriptions of UNESCO-led or UNESCO-supported studies
          </p>
          <h1 className="pls-hero-title">{data.title}</h1>
        </div>
        {heroCopyright && (
          // Server-side sanitized by Drupal's renderInIsolation pipeline.
          <div
            className="pls-hero-copyright"
            dangerouslySetInnerHTML={{ __html: heroCopyright }}
          />
        )}
      </section>

      {/* Body */}
      <div className="pls-container">
        <div className="pls-layout">
          <main className="pls-main">
            {sections.map((s) => (
              <section key={s.key} id={s.anchor} className="pls-section">
                <h2 className="pls-section-title">{s.title}</h2>
                <HTMLBlock html={data[s.key]} />
              </section>
            ))}

            {related.length > 0 && (
              <section id="related" className="pls-section">
                <h2 className="pls-section-title">You may be interested to read</h2>
                <div className="pls-related-list">
                  {related.map((r) => (
                    <article key={r.id} className="pls-related-card">
                      <h3 className="pls-related-title">{r.title}</h3>
                      <a className="pls-related-btn" href={`/pls/${r.id}`}>
                        <span>Read more</span>
                        <ArrowIcon className="pls-related-btn-icon" />
                      </a>
                    </article>
                  ))}
                </div>
              </section>
            )}

            {data.footnotes && (
              <section className="pls-section pls-footnotes">
                <HTMLBlock html={data.footnotes} />
              </section>
            )}
          </main>

          <aside className="pls-sidebar">
            {summaryItems.length > 0 && (
              <div className="pls-side-block">
                <h3 className="pls-side-title">Summary</h3>
                <ul className="pls-side-list">
                  {summaryItems.map((s) => (
                    <li key={s.anchor}>
                      <a
                        href={`#${s.anchor}`}
                        onClick={(e) => smoothScrollToAnchor(e, s.anchor)}
                      >
                        {s.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {(pub.link || authors.length > 0 || pub.sponsor_text || sponsorLogo) && (
              <div className="pls-side-block pls-pub-card">
                <div className="pls-pub-header">
                  <div className="pls-pub-heading">
                    <h3 className="pls-side-title">Original publication</h3>
                    <button
                      type="button"
                      className="pls-info"
                      aria-label="More information about the original publication link"
                    >
                      <InfoIcon />
                      <span className="pls-tooltip" role="tooltip">
                        You can find a link to access the full text of the original
                        publication under the Open Access section on the following page
                      </span>
                    </button>
                  </div>
                  {pub.link && (
                    <a
                      className="pls-open-btn"
                      href={pub.link}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <span>Open</span>
                      <ArrowIcon className="pls-open-btn-icon" />
                    </a>
                  )}
                </div>

                {authors.length > 0 && (
                  <>
                    <hr className="pls-card-divider" />
                    <h4 className="pls-authors-title">
                      Authors of the original publication:
                    </h4>
                    <p className="pls-author-list">
                      {authors.map((a, i) => (
                        <span className="pls-author" key={i}>
                          {a.link ? (
                            <a href={a.link} target="_blank" rel="noopener noreferrer">
                              {a.name}
                            </a>
                          ) : (
                            <span>{a.name}</span>
                          )}
                          {a.orcid && (
                            <a
                              className="pls-orcid"
                              href={`https://orcid.org/${a.orcid}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              aria-label={`${a.name}'s ORCID profile`}
                              title={`${a.name}'s ORCID profile`}
                            >
                              <img
                                className="pls-orcid-icon"
                                src="/static/images/orcid.svg"
                                alt="ORCID iD"
                              />
                            </a>
                          )}
                          {i < authors.length - 1 ? ", " : ""}
                        </span>
                      ))}
                    </p>
                  </>
                )}

                {(pub.sponsor_text || sponsorLogo) && (
                  <div className="pls-sponsor-block">
                    {pub.sponsor_text && (
                      <p className="pls-sponsor-text">{pub.sponsor_text}</p>
                    )}
                    {sponsorLogo && (
                      <img
                        className="pls-sponsor-logo"
                        src={sponsorLogo}
                        alt="Sponsor"
                      />
                    )}
                  </div>
                )}
              </div>
            )}

            {sdgs.length > 0 && (
              <div className="pls-side-block pls-card-outlined">
                <h3 className="pls-side-title pls-card-title">UN SDGs</h3>
                <div className="pls-sdgs">
                  {sdgs.map((s) => {
                    const logo = resolveCmsAsset(s.logo);
                    return (
                      <div
                        key={s.goal || s.text}
                        className="pls-sdg"
                        title={s.description || s.text}
                      >
                        {logo ? (
                          <img src={logo} alt={`SDG ${s.goal}: ${s.text}`} />
                        ) : (
                          <span className="pls-sdg-fallback">{s.goal || "•"}</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {tags.length > 0 && (
              <div className="pls-side-block pls-card-outlined">
                <h3 className="pls-side-title pls-card-title">Keywords and topics</h3>
                <div className="pls-tags">
                  {tags.map((t) => {
                    const description = t.description && t.description.trim();
                    return (
                      <span className="pls-tag" key={t.id}>
                        <a
                          className="pls-tag-link"
                          href={`/search?q=${encodeURIComponent(t.text)}`}
                        >
                          {t.text}
                        </a>
                        {description && (
                          <>
                            <button
                              type="button"
                              className="pls-tag-info"
                              aria-label={`Definition of ${t.text}`}
                            >
                              <InfoIcon />
                            </button>
                            <span className="pls-tooltip pls-tooltip--tag" role="tooltip">
                              {description}
                            </span>
                          </>
                        )}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </aside>
        </div>

        <div className="pls-jumpup-wrap">
          <button type="button" className="pls-jumpup" onClick={scrollToTop}>
            Jump up
          </button>
        </div>
      </div>
    </div>
  );
};

PlsDetail.propTypes = {};
