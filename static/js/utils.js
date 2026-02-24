/**
 * @file utils.js
 * @description Shared utility functions used across pages.
 *              Exposes a global `AppUtils` namespace.
 */

/* global window, document */

window.AppUtils = (() => {
    'use strict';

    /**
     * Read a cookie value by name (needed for Django CSRF).
     * @param {string} name - Cookie name.
     * @returns {string|null} Cookie value or null.
     */
    function getCookie(name) {
        if (!document.cookie) return null;

        const prefix = `${name}=`;
        const cookies = document.cookie.split(';');

        for (const raw of cookies) {
            const cookie = raw.trim();
            if (cookie.startsWith(prefix)) {
                return decodeURIComponent(cookie.substring(prefix.length));
            }
        }
        return null;
    }

    /**
     * Shorthand for `document.getElementById`.
     * @param {string} id
     * @returns {HTMLElement|null}
     */
    function byId(id) {
        return document.getElementById(id);
    }

    /**
     * Shorthand for `document.querySelector`.
     * @param {string} selector
     * @returns {Element|null}
     */
    function qs(selector) {
        return document.querySelector(selector);
    }

    /**
     * Shorthand for `document.querySelectorAll` → real Array.
     * @param {string} selector
     * @returns {Element[]}
     */
    function qsa(selector) {
        return Array.from(document.querySelectorAll(selector));
    }

    /**
     * Detect if the viewport is narrower than the mobile breakpoint.
     * @returns {boolean}
     */
    function isMobile() {
        return window.innerWidth <= (window.APP_CONFIG?.MOBILE_BREAKPOINT ?? 768);
    }

    return Object.freeze({ getCookie, byId, qs, qsa, isMobile });
})();
