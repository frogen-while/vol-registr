/**
 * @file register-page.js
 * @description Registration page: 3-step form with step navigation,
 *              validation, GSAP entrance animations,
 *              and JSON form submission.
 */

/* global gsap, document */

document.addEventListener('DOMContentLoaded', () => {
  // ── Language Support ─────────────────────────────
  // Use translation object from navbar.js
  const T = window.PA_TRANSLATIONS || (window.T || {});
  let lang = localStorage.getItem('pa_lang') || 'en';

  function applyLangReg(l) {
    lang = l;
    const t = T[l] || T.en || {};
    // Text content
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      if (t[key] !== undefined) el.innerHTML = t[key];
    });
    // Placeholders
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      const key = el.dataset.i18nPh;
      if (t[key] !== undefined) el.placeholder = t[key];
    });
  }

  // Listen for global language change
  window.addEventListener('pa_lang_change', e => {
    applyLangReg(e.detail);
  });
  // Initial language
  applyLangReg(lang);

  // -- Step State --
  let currentStep = 1;
  const TOTAL_STEPS = 3;
  const MIN_PLAYERS = 6;
  let playerCount = 6; // initial roster rows

  const panels = {
    1: document.getElementById('step1'),
    2: document.getElementById('step2'),
    3: document.getElementById('step3'),
    success: document.getElementById('stepSuccess'),
  };

  const stepperFill  = document.getElementById('stepperFill');
  const stepDots     = document.querySelectorAll('.reg-step');

  function updateStepper(step) {
    const pct = ((step - 1) / TOTAL_STEPS) * 100;
    if (stepperFill) stepperFill.style.width = pct + '%';

    stepDots.forEach(dot => {
      const n = parseInt(dot.dataset.step, 10);
      dot.classList.remove('active', 'done');
      if (n === step)      dot.classList.add('active');
      else if (n < step)   dot.classList.add('done');
    });
  }

  function showStep(next, direction = 1) {
    const prev = panels[currentStep];
    const nextPanel = panels[next];
    if (!nextPanel) return;

    // Animate out old
    if (prev) {
      gsap.to(prev, {
        opacity: 0,
        x: direction * -40,
        duration: 0.25,
        ease: 'power2.in',
        onComplete: () => {
          prev.classList.add('reg-panel--hidden');
          prev.style.removeProperty('opacity');
          prev.style.removeProperty('transform');
        },
      });
    }

    // Animate in new
    nextPanel.classList.remove('reg-panel--hidden');
    gsap.fromTo(nextPanel,
      { opacity: 0, x: direction * 40 },
      { opacity: 1, x: 0, duration: 0.35, ease: 'power2.out', delay: 0.2 },
    );

    currentStep = next;
    updateStepper(next);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // -- Validation Helpers --
  function setError(id, msg, msgKey, msgArg) {
    const el = document.getElementById('err-' + id);
    if (!el) return;
    let t = T[lang] || T.en || {};
    if (msgKey && t[msgKey]) {
      el.textContent = t[msgKey].replace('{n}', msgArg !== undefined ? msgArg : '');
    } else {
      el.textContent = msg;
    }
  }

  function clearErrors(...ids) {
    ids.forEach(id => setError(id, ''));
  }

  function markInputError(input, hasError) {
    input.classList.toggle('error', hasError);
  }

  // -- Step 1 Validation --
  function validateStep1() {
    clearErrors('teamName', 'leagueLevel');
    let ok = true;

    const teamName = document.getElementById('teamName');
    if (!teamName.value.trim()) {
      setError('teamName', '', 'err_team_name');
      markInputError(teamName, true);
      ok = false;
    } else {
      markInputError(teamName, false);
    }

    const selected = document.querySelector('input[name="leagueLevel"]:checked');
    if (!selected) {
      setError('leagueLevel', '', 'err_league');
      ok = false;
    }

    return ok;
  }

  // -- Step 2 Validation --
  function validateStep2() {
    clearErrors('capName', 'phone', 'email');
    let ok = true;

    const capName = document.getElementById('capName');
    if (!capName.value.trim() || capName.value.trim().indexOf(' ') === -1) {
      setError('capName', '', 'err_fullname');
      markInputError(capName, true);
      ok = false;
    } else {
      markInputError(capName, false);
    }

    const phone = document.getElementById('phone');
    if (!phone.value.trim()) {
      setError('phone', '', 'err_phone');
      markInputError(phone, true);
      ok = false;
    } else {
      markInputError(phone, false);
    }

    const email = document.getElementById('email');
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRe.test(email.value.trim())) {
      setError('email', '', 'err_email');
      markInputError(email, true);
      ok = false;
    } else {
      markInputError(email, false);
    }

    return ok;
  }

  // -- Step 3 Validation --
  function validateStep3() {
    clearErrors('checks');
    let ok = true;

    // Count filled-in players (first + last name present)
    const rows = document.querySelectorAll('.roster-row');
    let filledCount = 0;
    rows.forEach(row => {
      const first = row.querySelector('.roster-first');
      const last  = row.querySelector('.roster-last');
      const hasFirst = first && first.value.trim();
      const hasLast  = last && last.value.trim();

      if (hasFirst && hasLast) {
        filledCount++;
        markInputError(first, false);
        markInputError(last, false);
      } else if (hasFirst || hasLast) {
        // Partially filled - mark incomplete fields
        if (!hasFirst) markInputError(first, true);
        if (!hasLast)  markInputError(last, true);
      } else {
        // Completely empty - clear errors
        markInputError(first, false);
        markInputError(last, false);
      }
    });

    if (filledCount < MIN_PLAYERS) {
      setError('checks', '', 'err_players', filledCount);
      // Also mark empty required rows
      let marked = 0;
      rows.forEach(row => {
        if (marked >= MIN_PLAYERS) return;
        const first = row.querySelector('.roster-first');
        const last  = row.querySelector('.roster-last');
        if (!first.value.trim() || !last.value.trim()) {
          markInputError(first, !first.value.trim());
          markInputError(last, !last.value.trim());
        }
        marked++;
      });
      ok = false;
    }

    // Required checkboxes
    const chkTerms   = document.getElementById('chkTerms');
    const chkPayment = document.getElementById('chkPayment');

    if (!chkTerms.checked || !chkPayment.checked) {
      setError('checks', '', 'err_checks');
      ok = false;
    }

    return ok;
  }

  // -- Next / Back Buttons --
  document.querySelectorAll('.reg-btn--next').forEach(btn => {
    btn.addEventListener('click', () => {
      const next = parseInt(btn.dataset.next, 10);

      if (currentStep === 1 && !validateStep1()) return;
      if (currentStep === 2 && !validateStep2()) return;

      showStep(next, 1);
    });
  });

  document.querySelectorAll('.reg-btn--back').forEach(btn => {
    btn.addEventListener('click', () => {
      const prev = parseInt(btn.dataset.prev, 10);
      showStep(prev, -1);
    });
  });

  // -- Add Player Button --
  const addPlayerBtn = document.getElementById('addPlayerBtn');
  const rosterList   = document.getElementById('rosterList');

  if (addPlayerBtn && rosterList) {
    addPlayerBtn.addEventListener('click', () => {
      playerCount++;
      const row = document.createElement('div');
      row.className = 'roster-row';
      row.dataset.index = String(playerCount);
      row.innerHTML =
        '<div class="roster-row__num">' + playerCount + '</div>' +
        '<div class="roster-row__fields">' +
          '<input class="reg-input roster-first" type="text" placeholder="First Name" maxlength="50">' +
          '<input class="reg-input roster-last" type="text" placeholder="Last Name" maxlength="50">' +
          '<input class="reg-input roster-jersey" type="number" placeholder="#" min="0" max="99">' +
        '</div>';

      rosterList.appendChild(row);

      // Animate the new row in
      gsap.from(row, {
        opacity: 0,
        y: 15,
        duration: 0.35,
        ease: 'power2.out',
      });
    });
  }

  // -- Collect Roster --
  function collectPlayers() {
    const players = [];
    document.querySelectorAll('.roster-row').forEach(row => {
      const first  = row.querySelector('.roster-first')?.value.trim() || '';
      const last   = row.querySelector('.roster-last')?.value.trim()  || '';
      const jersey = row.querySelector('.roster-jersey')?.value || '';

      if (first && last) {
        players.push({
          firstName:    first,
          lastName:     last,
          jerseyNumber: jersey ? parseInt(jersey, 10) : null,
        });
      }
    });
    return players;
  }

  // -- Form Submit --
  const form       = document.getElementById('registrationForm');
  const submitBtn  = document.getElementById('submitBtn');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!validateStep3()) return;

    // Collect payload
    const leagueLevelEl = document.querySelector('input[name="leagueLevel"]:checked');

    const payload = {
      teamName:    document.getElementById('teamName')?.value.trim() || '',
      leagueLevel: leagueLevelEl ? leagueLevelEl.value : '',
      instagram:   document.getElementById('instagram')?.value.trim() || '',
      capName:     document.getElementById('capName')?.value.trim() || '',
      phone:       document.getElementById('phone')?.value.trim() || '',
      email:       document.getElementById('email')?.value.trim() || '',
      players:     collectPlayers(),
      lang:        localStorage.getItem('pa_lang') || 'en',
    };

    // Loading state
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    try {
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

      const res = await fetch('/api/register/', {
        method:  'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken':  csrfToken,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (data.success) {
        // Show success panel
        panels[currentStep].classList.add('reg-panel--hidden');
        const successPanel = panels.success;
        successPanel.classList.remove('reg-panel--hidden');
        gsap.fromTo(successPanel,
          { opacity: 0, scale: 0.95 },
          { opacity: 1, scale: 1, duration: 0.5, ease: 'back.out(1.5)' },
        );

        // Fill stepper to 100%
        if (stepperFill) stepperFill.style.width = '100%';
        stepDots.forEach(dot => dot.classList.replace('active', 'done') || dot.classList.add('done'));
      } else {
        setError('checks', data.error || '', 'err_failed');
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
      }
    } catch (err) {
      setError('checks', '', 'err_network');
      submitBtn.classList.remove('loading');
      submitBtn.disabled = false;
    }
  });

  // -- Entrance Animations --
  gsap.from('.reg-brand__hero', {
    opacity: 0,
    y: 30,
    duration: 0.7,
    ease: 'power2.out',
    delay: 0.1,
  });

  gsap.from('.reg-stepper', {
    opacity: 0,
    y: 20,
    duration: 0.6,
    ease: 'power2.out',
    delay: 0.3,
  });

  gsap.from('.reg-panel:not(.reg-panel--hidden)', {
    opacity: 0,
    y: 25,
    duration: 0.6,
    ease: 'power2.out',
    delay: 0.2,
  });

  // Initial stepper state
  updateStepper(1);

  // -- Promo Flip Card --
  (function initPromoCard() {
    const photos = window.REG_CARD_PHOTOS;
    if (!photos || !photos.length) return;

    const card = document.getElementById('regFlipCard');
    const img  = document.getElementById('regPromoPhoto');
    if (!card || !img) return;

    let lastIdx = -1;
    function nextPhoto() {
      let idx;
      do { idx = Math.floor(Math.random() * photos.length); }
      while (idx === lastIdx && photos.length > 1);
      lastIdx = idx;
      return photos[idx];
    }

    // Start with a random photo (back is showing at 0deg)
    img.src = nextPhoto();

    // Continuous spin: back at 0-180, front at 180-360
    // Swap photo silently at the start of each cycle while back faces viewer
    card.style.transition = 'none'; // override CSS transition - GSAP owns this
    gsap.to(card, {
      rotationY: '+=360',
      duration: 5,
      ease: 'none',
      repeat: -1,
      onRepeat: function () {
        // Back is facing - load next photo quietly
        img.src = nextPhoto();
      },
    });
  })();
});
