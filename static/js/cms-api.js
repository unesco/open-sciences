/**
 * CMS API helper — shared across header, footer, and static pages.
 *
 * In dev (localhost / 127.0.0.1) the CMS runs on :8080.
 * In prod, nginx proxies /cms so no host prefix is needed.
 *
 * Usage:
 *   CmsApi.fetch('/footer').then(function(data) { ... });
 *   CmsApi.fetch('/homepage/cards').then(function(data) { ... });
 *   CmsApi.fetchRaw('/pls').then(function(items) { ... });
 *   CmsApi.resolveAsset('/cms/sites/default/files/img.png');
 *
 * fetch()      — resolves with result.data (standard CMS envelope)
 * fetchRaw()   — resolves with the full parsed JSON (for endpoints that return arrays)
 * resolveAsset() — converts a CMS-relative image path to an absolute URL
 */
(function(global) {
  'use strict';

  // Host resolution, identical to site/my_site/assets/pages/*/api.js:
  // in dev (localhost/127.0.0.1 on a non-standard port) the CMS runs at :8080;
  // in prod nginx proxies /cms on the same origin, so the prefix is empty.
  var isDev =
    (window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1') &&
    window.location.port !== '' &&
    window.location.port !== '80' &&
    window.location.port !== '443';
  var CMS_ORIGIN = isDev ? 'http://localhost:8080' : '';
  var BASE_URL = CMS_ORIGIN + '/cms/api';

  function _doFetch(endpoint, lang) {
    var language = lang || document.documentElement.lang || 'en';
    var url = BASE_URL + endpoint + '?lang=' + language;
    return fetch(url, { headers: { Accept: 'application/json' } })
      .then(function(r) {
        if (!r.ok) throw new Error('CMS API error: ' + r.status + ' ' + url);
        return r.json();
      });
  }

  // Extract the page slug from a CMS link url:
  // '/cms/api/pages/about' -> 'about'. Strips query/hash and trailing slashes.
  function _pageSlug(url) {
    var path = String(url || '').split('?')[0].split('#')[0].replace(/\/+$/, '');
    return path.substring(path.lastIndexOf('/') + 1);
  }

  var CmsApi = {
    /**
     * Fetch a CMS endpoint that returns the standard { data, lang, ... } envelope.
     * @param {string} endpoint  Path relative to /cms/api, e.g. '/homepage/cards'
     * @param {string} [lang]    Language code; defaults to the HTML lang attribute or 'en'
     * @returns {Promise<object>} Resolves with result.data
     */
    fetch: function(endpoint, lang) {
      return _doFetch(endpoint, lang).then(function(result) {
        return result.data || {};
      });
    },

    /**
     * Fetch a CMS endpoint that returns a raw value (e.g. an array).
     * @param {string} endpoint  Path relative to /cms/api, e.g. '/pls'
     * @param {string} [lang]    Language code; defaults to the HTML lang attribute or 'en'
     * @returns {Promise<any>} Resolves with the full parsed JSON
     */
    fetchRaw: function(endpoint, lang) {
      return _doFetch(endpoint, lang);
    },

    /**
     * Fetch a single CMS page by slug. Returns the raw { title, body } object.
     * Used by the React CMS page (/page#<slug>).
     * @param {string} slug   e.g. 'about'
     * @param {string} [lang] Language code; defaults to the HTML lang attribute or 'en'
     * @returns {Promise<{title: string, body: string}>}
     */
    fetchPage: function(slug, lang) {
      var language = lang || document.documentElement.lang || 'en';
      var url = BASE_URL + '/pages/' + encodeURIComponent(slug) + '?lang=' + language;
      return fetch(url, { headers: { Accept: 'application/json' } })
        .then(function(r) {
          if (r.status === 404) {
            var e = new Error('Not found');
            e.status = 404;
            throw e;
          }
          if (!r.ok) throw new Error('CMS page error: ' + r.status + ' ' + url);
          return r.json();
        });
    },

    /**
     * Resolve a CMS-relative asset path to an absolute URL.
     * Handles /cms/... paths, bare /... paths, absolute URLs, and empty values.
     * @param {string} path  e.g. '/cms/sites/default/files/img.png'
     * @returns {string}
     */
    resolveAsset: function(path) {
      if (!path) return '';
      if (/^https?:\/\//i.test(path)) return path;
      if (path.indexOf('/cms/') === 0) return CMS_ORIGIN + path;
      if (path.charAt(0) === '/') return CMS_ORIGIN + '/cms' + path;
      return path;
    },

    /**
     * Resolve a CMS link object { external, url } to an href string.
     * External links keep their url; internal CMS page links point to the
     * React CMS page '/page#<slug>' (slug taken from the url's last segment).
     * @param {{external?: boolean, url?: string}} link
     * @returns {string}
     */
    resolveLinkHref: function(link) {
      if (!link || !link.url) return '#';
      if (link.external) return link.url;
      var slug = _pageSlug(link.url);
      return slug ? ('/page#' + slug) : link.url;
    },

    /**
     * Configure an <a> element for a CMS link object { external, label, url }.
     * If external is true, the link opens in a new tab. Otherwise the url is a
     * CMS page API endpoint (e.g. '/cms/api/pages/about'); the link points to
     * the React CMS page '/page#<slug>', which fetches and renders { title, body }.
     * @param {HTMLAnchorElement} anchor
     * @param {{external?: boolean, label?: string, url?: string}} link
     * @returns {HTMLAnchorElement} the same anchor, for chaining
     */
    applyLink: function(anchor, link) {
      if (!anchor || !link) return anchor;
      anchor.href = CmsApi.resolveLinkHref(link);
      if (link.external) {
        anchor.target = '_blank';
        anchor.rel = 'noopener noreferrer';
      }
      return anchor;
    }
  };

  global.CmsApi = CmsApi;
})(window);
