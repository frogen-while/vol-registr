/**
 * @file config.js
 * @description Centralized configuration for GSAP animation timings,
 *              easing curves, breakpoints, and API endpoints.
 *              Change values here instead of digging through animation code.
 */

/* global window */

window.APP_CONFIG = Object.freeze({

    /* ── Breakpoints ──────────────────────────────── */
    MOBILE_BREAKPOINT: 768,

    /* ── API Routes ───────────────────────────────── */
    API_REGISTER_URL: '/api/register/',

    /* ── Hero Section Timings ─────────────────────── */
    hero: {
        logo:       { duration: 1.0, ease: 'power3.out' },
        title:      { duration: 1.2, stagger: 0.15, ease: 'power4.out' },
        label:      { duration: 0.8, ease: 'power3.out' },
        text:       { duration: 1.0, stagger: 0.2, ease: 'power2.out' },
        player:     { duration: 1.5, ease: 'power3.out', mobileOpacity: 0.3 },
        scroll:     { duration: 1.0, delay: 0.5 },
    },

    /* ── Flip Cards ───────────────────────────────── */
    cards: {
        flyIn: {
            duration: 0.6,
            stagger: 0.05,
            ease: 'none',
        },
        flip: {
            duration: 1.2,
            stagger: 0.08,
            ease: 'power3.inOut',
        },
        /** Random position range multiplier. */
        randomOffset: { min: 120, max: 260 },
        randomRotation: { min: -25, max: 25 },
        scrollStart: 'top 80%',
    },

    /* ── Scroll Animations ────────────────────────── */
    scroll: {
        locationSlide: { x: 50, duration: 1, start: 'top 80%' },
        timelineItem:  { y: 30, duration: 0.8, start: 'top 85%' },
    },

    /* ── Registration Page ────────────────────────── */
    registration: {
        introHeroText:  { y: 40, duration: 1.0, stagger: 0.15, ease: 'power3.out' },
        formPanel:      { x: 50, duration: 1.0, ease: 'power3.out' },
        formField:      { y: 20, duration: 0.8, stagger: 0.1, ease: 'power2.out' },
        passReveal:     { scale: 0.5, rotateX: -30, duration: 1.5, ease: 'back.out(1.5)' },

        /** Idle floating animation for the VIP pass. */
        passFloat:      { y: -15, duration: 3, ease: 'sine.inOut' },
        passSpin:       { duration: 15, ease: 'none' },
        passMouseTilt:  { multiplier: 0.1, duration: 0.5, ease: 'power1.out' },
        passResetDelay: 0.5,

        /** Form submission animations. */
        hideFields:     { y: -20, duration: 0.4, stagger: 0.05, ease: 'power2.in' },
        successReveal:  { duration: 0.6, ease: 'back.out(1.5)' },
        celebrationSpin: 720,
    },
});
