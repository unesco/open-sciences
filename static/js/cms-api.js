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

  // CMS is served from the same origin under /cms (nginx proxies in prod,
  // Flask serves it locally), so no host prefix is needed.
  var CMS_ORIGIN = '';
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
    }
  };

  global.CmsApi = CmsApi;
})(window);
