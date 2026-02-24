/**
 * @file register-page.js
 * @description Registration page: intro animations, VIP pass 3D,
 *              and form submission logic.
 *              Depends on: config.js, utils.js, gsap (CDN).
 */

/* global gsap, window, document, APP_CONFIG, AppUtils */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    const CFG = window.APP_CONFIG.registration;

    initRegistrationIntro(CFG);
    initPassIdleAnimation(CFG);
    initPassMouseInteraction(CFG);
    initFormSubmission(CFG);
});


// ═══════════════════════════════════════════════════════
//  Intro Timeline
// ═══════════════════════════════════════════════════════

/**
 * Animate the page elements in on load.
 * @param {object} cfg
 */
function initRegistrationIntro(cfg) {
    const tl = gsap.timeline();

    // Hero text
    tl.from('.gsap-hero-text > *', {
        y: cfg.introHeroText.y,
        opacity: 0,
        duration: cfg.introHeroText.duration,
        stagger: cfg.introHeroText.stagger,
        ease: cfg.introHeroText.ease,
    });

    // Form panel
    tl.from('.gsap-form-panel', {
        x: cfg.formPanel.x,
        opacity: 0,
        duration: cfg.formPanel.duration,
        ease: cfg.formPanel.ease,
    }, '-=0.8');

    // Form fields cascade
    tl.from('.gsap-form-field', {
        y: cfg.formField.y,
        opacity: 0,
        duration: cfg.formField.duration,
        stagger: cfg.formField.stagger,
        ease: cfg.formField.ease,
    }, '-=0.6');

    // VIP pass
    tl.from('.gsap-pass', {
        scale: cfg.passReveal.scale,
        opacity: 0,
        rotateX: cfg.passReveal.rotateX,
        duration: cfg.passReveal.duration,
        ease: cfg.passReveal.ease,
    }, '-=1');
}


// ═══════════════════════════════════════════════════════
//  VIP Pass — Idle Levitation & Spin
// ═══════════════════════════════════════════════════════

/**
 * Continuous float + slow Y-axis rotation.
 * @param {object} cfg
 */
function initPassIdleAnimation(cfg) {
    gsap.to('.pass-container', {
        y: cfg.passFloat.y,
        duration: cfg.passFloat.duration,
        repeat: -1,
        yoyo: true,
        ease: cfg.passFloat.ease,
    });

    gsap.to('#vipPass', {
        rotateY: 360,
        duration: cfg.passSpin.duration,
        repeat: -1,
        ease: cfg.passSpin.ease,
    });
}


// ═══════════════════════════════════════════════════════
//  VIP Pass — Mouse Tilt Interaction
// ═══════════════════════════════════════════════════════

/**
 * Pause spin on hover and tilt card toward pointer.
 * @param {object} cfg
 */
function initPassMouseInteraction(cfg) {
    const passElement  = AppUtils.byId('vipPass');
    const passContainer = AppUtils.qs('.pass-container');
    if (!passContainer || !passElement) return;

    const tilt = cfg.passMouseTilt;

    passContainer.addEventListener('mousemove', (e) => {
        const rect = passContainer.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width  / 2;
        const y = e.clientY - rect.top  - rect.height / 2;

        gsap.killTweensOf(passElement, 'rotateY');

        gsap.to(passElement, {
            rotateY:  x * tilt.multiplier,
            rotateX: -y * tilt.multiplier,
            duration: tilt.duration,
            ease: tilt.ease,
        });
    });

    passContainer.addEventListener('mouseleave', () => {
        gsap.to(passElement, {
            rotateX: 0,
            rotateY: '+=360',
            duration: cfg.passSpin.duration,
            repeat: -1,
            ease: cfg.passSpin.ease,
            delay: cfg.passResetDelay,
        });
    });
}


// ═══════════════════════════════════════════════════════
//  Form Submission
// ═══════════════════════════════════════════════════════

/**
 * Attach submit handler: collects data, sends to API, shows result.
 * @param {object} cfg
 */
function initFormSubmission(cfg) {
    const form           = AppUtils.byId('registrationForm');
    const submitBtn      = AppUtils.byId('submitBtn');
    const successMessage = AppUtils.byId('successMessage');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const originalHTML = submitBtn.innerHTML;
        setButtonLoading(submitBtn, true);

        const payload = collectFormData();
        const csrfToken = AppUtils.getCookie('csrftoken');

        try {
            const result = await sendRegistration(payload, csrfToken);

            if (result.success) {
                showSuccessAnimation(cfg, successMessage);
            } else {
                alert(`Registration Error: ${result.error}`);
                setButtonLoading(submitBtn, false, originalHTML);
            }
        } catch (err) {
            console.error('Registration request failed:', err);
            alert('An error occurred. Please try again.');
            setButtonLoading(submitBtn, false, originalHTML);
        }
    });
}

/**
 * Collect data from DOM form fields.
 * @returns {object} Registration payload.
 */
function collectFormData() {
    return {
        teamName: AppUtils.byId('teamName').value,
        division: AppUtils.byId('division').value,
        city:     AppUtils.byId('city').value,
        capName:  AppUtils.byId('capName').value,
        phone:    AppUtils.byId('phone').value,
        email:    AppUtils.byId('email').value,
        roster:   AppUtils.byId('roster').value,
    };
}

/**
 * POST registration data to the API endpoint.
 * @param {object} data
 * @param {string} csrfToken
 * @returns {Promise<object>} Parsed JSON response.
 */
async function sendRegistration(data, csrfToken) {
    const url = window.APP_CONFIG.API_REGISTER_URL;

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(data),
    });

    return response.json();
}

/**
 * Toggle the submit button between normal and loading states.
 * @param {HTMLElement} btn
 * @param {boolean} loading
 * @param {string} [html] - Original innerHTML to restore.
 */
function setButtonLoading(btn, loading, html) {
    if (loading) {
        btn.innerHTML = '<span class="btn-submit__text">Processing...</span>';
        btn.style.opacity = '0.8';
        btn.disabled = true;
    } else {
        btn.innerHTML = html;
        btn.style.opacity = '1';
        btn.disabled = false;
    }
}

/**
 * Animate form fields out, show success message, celebrate with the pass.
 * @param {object} cfg
 * @param {HTMLElement} successEl
 */
function showSuccessAnimation(cfg, successEl) {
    gsap.to('.gsap-form-field', {
        y: cfg.hideFields.y,
        opacity: 0,
        duration: cfg.hideFields.duration,
        stagger: cfg.hideFields.stagger,
        ease: cfg.hideFields.ease,
        onComplete() {
            // Hide form fields
            AppUtils.qsa('.gsap-form-field').forEach(f => f.classList.add('hidden'));

            // Reveal success message
            successEl.classList.remove('hidden');
            gsap.from(successEl, {
                scale: 0.9,
                opacity: 0,
                duration: cfg.successReveal.duration,
                ease: cfg.successReveal.ease,
            });

            // VIP pass celebration spin
            gsap.to('#vipPass', {
                rotateY: `+=${cfg.celebrationSpin}`,
                duration: 2,
                ease: 'power2.inOut',
                onComplete() {
                    gsap.to('#vipPass', {
                        rotateY: '+=360',
                        duration: cfg.passSpin.duration,
                        repeat: -1,
                        ease: cfg.passSpin.ease,
                    });
                },
            });
        },
    });
}
