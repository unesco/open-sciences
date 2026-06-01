/**
 * CMS API helper — shared across header, footer, and static pages.
 *
 * In dev (localhost / 127.0.0.1) the CMS runs on :8080.
 * In prod, nginx proxies /cms so no host prefix is needed.
 *
 * Usage:
 *   CmsApi.fetch('/footer').then(function(data) { ... });
 *   CmsApi.fetch('/homepage/header').then(function(data) { ... });
 *   CmsApi.fetch('/privacy_page').then(function(data) { ... });
 *
 * The promise resolves with `result.data` from the JSON response,
 * or rejects on a non-OK response or network error.
 */
(function(global) {
  'use strict';

  var isDev = global.location.hostname === 'localhost' ||
              global.location.hostname === '127.0.0.1';

  var BASE_URL = (isDev ? 'http://localhost:8080' : '') + '/cms/api';

  var CmsApi = {
    /**
     * Fetch a CMS endpoint.
     * @param {string} endpoint  Path relative to /cms/api, e.g. '/footer'
     * @param {string} [lang]    Language code; defaults to the HTML lang attribute or 'en'
     * @returns {Promise<object>} Resolves with result.data
     */
    fetch: function(endpoint, lang) {
      var language = lang || document.documentElement.lang || 'en';
      var url = BASE_URL + endpoint + '?lang=' + language;
      return fetch(url, { headers: { Accept: 'application/json' } })
        .then(function(r) {
          if (!r.ok) throw new Error('CMS API error: ' + r.status + ' ' + url);
          return r.json();
        })
        .then(function(result) {
          return result.data || {};
        });
    }
  };

  global.CmsApi = CmsApi;
})(window);
