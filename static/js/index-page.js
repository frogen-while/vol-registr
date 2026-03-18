/**
 * @file index-page.js
 * @description GSAP animations for the landing page (index.html).
 *              Reads all timings/easing from APP_CONFIG.
 *              Depends on: config.js, utils.js, gsap + ScrollTrigger (CDN).
 */

/* global gsap, ScrollTrigger, window, APP_CONFIG, AppUtils */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    const CFG = window.APP_CONFIG;
    const isMobileView = window.matchMedia('(max-width: 768px)').matches;

    // ─── Hero Intro Timeline ────────────────────────
    initHeroIntro(CFG.hero);

    // ─── Card Modal (desktop only) ────────────────────
    if (!isMobileView) {
        initCardModal();
    }

    // ─── Registered Teams Modal ───────────────────────
    initRegisteredTeamsModal();

    // ─── Scroll-triggered Sections ──────────────────
    if (typeof ScrollTrigger !== 'undefined') {
        gsap.registerPlugin(ScrollTrigger);

        // Skip scroll animations on mobile
        if (!isMobileView) {
            initCardsFlyIn(CFG.cards);
            initLocationScrollAnim(CFG.scroll);
            initTimelineScrollAnim(CFG.scroll);
        }
    }
});


// ═══════════════════════════════════════════════════════
//  Hero Section
// ═══════════════════════════════════════════════════════

/**
 * Build the intro GSAP timeline for the hero section.
 * @param {object} cfg - hero timings from APP_CONFIG.
 */
function initHeroIntro(cfg) {
    const tl = gsap.timeline();

    // Logo
    tl.to('.hero-logo', {
        y: 0, opacity: 1,
        duration: cfg.logo.duration,
        ease: cfg.logo.ease,
    });

    // Title lines (staggered)
    tl.to('.hero-title > *', {
        y: 0, opacity: 1,
        duration: cfg.title.duration,
        stagger: cfg.title.stagger,
        ease: cfg.title.ease,
    }, '-=0.5');

    // Date / location label
    tl.to('.hero-label', {
        y: 0, opacity: 1,
        duration: cfg.label.duration,
        ease: cfg.label.ease,
    }, '-=1');

    // Subtitle, price, counter, CTA
    tl.to(['.hero-text', '.hero-price', '.hero-counter', '.hero-btn-container'], {
        y: 0, opacity: 1,
        duration: cfg.text.duration,
        stagger: cfg.text.stagger,
        ease: cfg.text.ease,
    }, '-=0.8');

    // Player image
    animateHeroPlayer(tl, cfg.player);

    // Scroll indicator
    tl.from('.scroll-indicator', {
        opacity: 0, y: -20,
        duration: cfg.scroll.duration,
        delay: cfg.scroll.delay,
    });
}

/**
 * Animate the hero player image (slide on desktop, fade on mobile).
 * @param {gsap.core.Timeline} tl
 * @param {object} cfg - player timing config.
 */
function animateHeroPlayer(tl, cfg) {
    if (AppUtils.isMobile()) {
        gsap.set('.hero-player', { x: 0 });
        tl.to('.hero-player', {
            opacity: cfg.mobileOpacity,
            duration: cfg.duration,
            ease: cfg.ease,
        }, '-=1.5');
    } else {
        tl.to('.hero-player', {
            x: 0, opacity: 1,
            duration: cfg.duration,
            ease: cfg.ease,
        }, '-=1.5');
    }
}


// ═══════════════════════════════════════════════════════
//  Flip Cards (Scroll-Triggered)
// ═══════════════════════════════════════════════════════

/**
 * Scatter cards off-screen, then fly + flip them on scroll.
 * @param {object} cfg - cards config from APP_CONFIG.
 */
function initCardsFlyIn(cfg) {
    const wrappers = gsap.utils.toArray('.flip-card-wrapper');
    const cards    = gsap.utils.toArray('.flip-card');
    if (!wrappers.length) return;

    scatterCardsOffScreen(wrappers, cfg);

    // Cards start with back visible (rotationY 0)
    gsap.set(cards, { rotationY: 0 });

    const cardsTl = gsap.timeline({
        scrollTrigger: {
            trigger: '.perspective-section',
            start: cfg.scrollStart,
            toggleActions: 'play none none none',
            once: true,
        },
    });

    // Step 1 — Fly to grid position
    cardsTl.to(wrappers, {
        x: 0, y: 0, rotation: 0, scale: 1,
        duration: cfg.flyIn.duration,
        stagger: { each: cfg.flyIn.stagger, from: 0 },
        ease: cfg.flyIn.ease,
    });

    // Step 2 — Flip to front
    cardsTl.to(cards, {
        rotationY: 180,
        duration: cfg.flip.duration,
        stagger: cfg.flip.stagger,
        ease: cfg.flip.ease,
        onComplete() {
            wrappers.forEach(w => {
                const card = w.querySelector('.flip-card');
                if (card) card.flipped = true;
            });
        },
    }, '-=0.8');
}

/**
 * Place each card wrapper at a random off-screen position.
 * @param {Element[]} wrappers
 * @param {object} cfg
 */
function scatterCardsOffScreen(wrappers, cfg) {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const { min: offMin, max: offMax } = cfg.randomOffset;
    const { min: rotMin, max: rotMax } = cfg.randomRotation;

    wrappers.forEach((wrapper, index) => {
        const side = index === 0
            ? 1                               // first → right
            : index === wrappers.length - 1
                ? 0                           // last  → left
                : Math.floor(Math.random() * 4);

        const offset = gsap.utils.random(offMin, offMax);
        let x = 0;
        let y = 0;

        switch (side) {
            case 0: x = -vw - offset; y = gsap.utils.random(-vh * 0.2, vh * 1.2); break;  // left
            case 1: x =  vw + offset; y = gsap.utils.random(-vh * 0.2, vh * 1.2); break;  // right
            case 2: y = -vh - offset; x = gsap.utils.random(-vw * 0.2, vw * 1.2); break;  // top
            default: y = vh + offset; x = gsap.utils.random(-vw * 0.2, vw * 1.2); break;  // bottom
        }

        gsap.set(wrapper, {
            x, y,
            opacity: 1,
            rotation: gsap.utils.random(rotMin, rotMax),
            scale: 0.98,
            force3D: true,
        });
    });
}


// ═══════════════════════════════════════════════════════
//  Location & Timeline Sections
// ═══════════════════════════════════════════════════════

/**
 * Slide-in animation for the location block.
 * @param {object} cfg - scroll config from APP_CONFIG.
 */
function initLocationScrollAnim(cfg) {
    const loc = cfg.locationSlide;

    gsap.from('.location-content', {
        scrollTrigger: { trigger: '.location-content', start: loc.start },
        x: -loc.x, opacity: 0, duration: loc.duration,
    });

    gsap.from('.location-map', {
        scrollTrigger: { trigger: '.location-content', start: loc.start },
        x: loc.x, opacity: 0, duration: loc.duration,
    });
}

/**
 * Staggered reveal for each timeline milestone.
 * @param {object} cfg - scroll config from APP_CONFIG.
 */
function initTimelineScrollAnim(cfg) {
    const item = cfg.timelineItem;

    gsap.utils.toArray('.timeline-item').forEach(el => {
        gsap.from(el, {
            scrollTrigger: { trigger: el, start: item.start },
            y: item.y, opacity: 0, duration: item.duration,
        });
    });
}


// ═══════════════════════════════════════════════════════
//  Card Modal (Desktop)
// ═══════════════════════════════════════════════════════

/**
 * Click a card → show its front face enlarged in a centered modal
 * with a blurred backdrop. Click overlay or press Escape to close.
 */
function initCardModal() {
    const overlay  = document.getElementById('cardModalOverlay');
    const modalBox = document.getElementById('cardModalCard');
    if (!overlay || !modalBox) return;

    // Click on any card wrapper → open modal
    document.querySelectorAll('.flip-card-wrapper').forEach(wrapper => {
        wrapper.addEventListener('click', (e) => {
            e.stopPropagation();
            const front = wrapper.querySelector('.flip-card-front');
            if (!front) return;

            // Clone front face into modal
            const clone = front.cloneNode(true);
            modalBox.innerHTML = '';
            modalBox.appendChild(clone);

            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    });

    // Close on overlay click
    overlay.addEventListener('click', () => closeCardModal(overlay));

    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('active')) {
            closeCardModal(overlay);
        }
    });
}

function closeCardModal(overlay) {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
}

// ═══════════════════════════════════════════════════════
//  Registered Teams Modal
// ═══════════════════════════════════════════════════════

/**
 * Click the 'Registered Teams' button to open a modal
 * showing the list of teams.
 */
function initRegisteredTeamsModal() {
    const modal = document.getElementById('registeredTeamsModal');
    const openBtn = document.getElementById('registeredTeamsBtn');
    const closeBtn = document.getElementById('registeredTeamsModalClose');

    if (!modal || !openBtn || !closeBtn) {
        return;
    }

    // Open modal
    openBtn.addEventListener('click', () => {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    });

    // Close via button
    closeBtn.addEventListener('click', () => {
        closeModal();
    });

    // Close via overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Close via Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });

    function closeModal() {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}
