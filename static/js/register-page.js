/**
 * @file register-page.js
 * @description Registration page: 3-step form with step navigation,
 *              validation, DOB selects, GSAP entrance animations,
 *              and JSON form submission.
 */

/* global gsap, document */

document.addEventListener('DOMContentLoaded', () => {

  // â”€â”€ DOB Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const MONTHS = [
    'January','February','March','April','May','June',
    'July','August','September','October','November','December',
  ];
  const CURRENT_YEAR = new Date().getFullYear();

  function populateDobSelects(dayEl, monthEl, yearEl, minAge = 14) {
    if (!dayEl || !monthEl || !yearEl) return;

    // Days 1-31
    for (let d = 1; d <= 31; d++) {
      const o = new Option(String(d).padStart(2, '0'), String(d));
      dayEl.appendChild(o);
    }

    // Months
    MONTHS.forEach((name, idx) => {
      monthEl.appendChild(new Option(name, String(idx + 1)));
    });

    // Years (current year â€“ minAge down to 1940)
    for (let y = CURRENT_YEAR - minAge; y >= 1940; y--) {
      yearEl.appendChild(new Option(String(y), String(y)));
    }
  }

  // Captain DOB
  populateDobSelects(
    document.getElementById('capDobDay'),
    document.getElementById('capDobMonth'),
    document.getElementById('capDobYear'),
    16,
  );

  // Roster DOBs
  document.querySelectorAll('.roster-dob').forEach(row => {
    populateDobSelects(
      row.querySelector('.roster-dob-day'),
      row.querySelector('.roster-dob-month'),
      row.querySelector('.roster-dob-year'),
      14,
    );
  });

  // â”€â”€ Step State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  let currentStep = 1;
  const TOTAL_STEPS = 3;

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

  // â”€â”€ Validation Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  function setError(id, msg) {
    const el = document.getElementById('err-' + id);
    if (!el) return;
    el.textContent = msg;
  }

  function clearErrors(...ids) {
    ids.forEach(id => setError(id, ''));
  }

  function markInputError(input, hasError) {
    input.classList.toggle('error', hasError);
  }

  // â”€â”€ Step 1 Validation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  function validateStep1() {
    clearErrors('teamName', 'leagueLevel');
    let ok = true;

    const teamName = document.getElementById('teamName');
    if (!teamName.value.trim()) {
      setError('teamName', 'Team name is required.');
      markInputError(teamName, true);
      ok = false;
    } else {
      markInputError(teamName, false);
    }

    const selected = document.querySelector('input[name="leagueLevel"]:checked');
    if (!selected) {
      setError('leagueLevel', 'Please select a league level.');
      ok = false;
    }

    return ok;
  }

  // â”€â”€ Step 2 Validation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  function validateStep2() {
    clearErrors('capName', 'phone', 'email');
    let ok = true;

    const capName = document.getElementById('capName');
    if (!capName.value.trim() || capName.value.trim().indexOf(' ') === -1) {
      setError('capName', 'Please enter first and last name.');
      markInputError(capName, true);
      ok = false;
    } else {
      markInputError(capName, false);
    }

    const phone = document.getElementById('phone');
    if (!phone.value.trim()) {
      setError('phone', 'Phone number is required.');
      markInputError(phone, true);
      ok = false;
    } else {
      markInputError(phone, false);
    }

    const email = document.getElementById('email');
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRe.test(email.value.trim())) {
      setError('email', 'Please enter a valid email address.');
      markInputError(email, true);
      ok = false;
    } else {
      markInputError(email, false);
    }

    return ok;
  }

  // â”€â”€ Step 3 Validation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  function validateStep3() {
    clearErrors('checks');
    let ok = true;

    // 4 required players
    const rows = document.querySelectorAll('.roster-row:not(.roster-row--sub)');
    let missingPlayer = false;
    rows.forEach(row => {
      const first = row.querySelector('.roster-first');
      const last  = row.querySelector('.roster-last');
      if (!first.value.trim() || !last.value.trim()) {
        markInputError(first, !first.value.trim());
        markInputError(last,  !last.value.trim());
        missingPlayer = true;
      } else {
        markInputError(first, false);
        markInputError(last, false);
      }
    });
    if (missingPlayer) {
      ok = false;
    }

    // Required checkboxes
    const chkTerms   = document.getElementById('chkTerms');
    const chkAge     = document.getElementById('chkAge');
    const chkPayment = document.getElementById('chkPayment');

    if (!chkTerms.checked || !chkAge.checked || !chkPayment.checked) {
      setError('checks', 'Please accept all required checkboxes to continue.');
      ok = false;
    }

    return ok;
  }

  // â”€â”€ Next / Back Buttons â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

  // â”€â”€ Collect DOB â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  function collectDob(dayEl, monthEl, yearEl) {
    const d = dayEl   ? dayEl.value   : '';
    const m = monthEl ? monthEl.value : '';
    const y = yearEl  ? yearEl.value  : '';
    if (!d || !m || !y) return null;
    return `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
  }

  // â”€â”€ Collect Roster â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  function collectPlayers() {
    const players = [];
    document.querySelectorAll('.roster-row').forEach(row => {
      const first  = row.querySelector('.roster-first')?.value.trim() || '';
      const last   = row.querySelector('.roster-last')?.value.trim()  || '';
      const jersey = row.querySelector('.roster-jersey')?.value || '';
      const dob    = collectDob(
        row.querySelector('.roster-dob-day'),
        row.querySelector('.roster-dob-month'),
        row.querySelector('.roster-dob-year'),
      );

      if (first) {
        players.push({
          firstName:    first,
          lastName:     last,
          jerseyNumber: jersey ? parseInt(jersey, 10) : null,
          dob:          dob,
        });
      }
    });
    return players;
  }

  // â”€â”€ Form Submit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const form       = document.getElementById('registrationForm');
  const submitBtn  = document.getElementById('submitBtn');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!validateStep3()) return;

    // Collect payload
    const leagueLevelEl = document.querySelector('input[name="leagueLevel"]:checked');
    const capDob = collectDob(
      document.getElementById('capDobDay'),
      document.getElementById('capDobMonth'),
      document.getElementById('capDobYear'),
    );

    const payload = {
      teamName:    document.getElementById('teamName')?.value.trim() || '',
      leagueLevel: leagueLevelEl ? leagueLevelEl.value : '',
      city:        document.getElementById('city')?.value.trim() || '',
      instagram:   document.getElementById('instagram')?.value.trim() || '',
      capName:     document.getElementById('capName')?.value.trim() || '',
      capDob:      capDob,
      capJersey:   document.getElementById('capJersey')?.value
                     ? parseInt(document.getElementById('capJersey').value, 10)
                     : null,
      phone:       document.getElementById('phone')?.value.trim() || '',
      email:       document.getElementById('email')?.value.trim() || '',
      players:     collectPlayers(),
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
        setError('checks', data.error || 'Registration failed. Please try again.');
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
      }
    } catch (err) {
      setError('checks', 'Network error. Please check your connection and try again.');
      submitBtn.classList.remove('loading');
      submitBtn.disabled = false;
    }
  });

  // â”€â”€ Entrance Animations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

  // ── Promo Flip Card ──────────────────────────────────────
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

    // Start with a random photo (back is showing at 0°)
    img.src = nextPhoto();

    // Continuous spin: back at 0°–180°, front at 180°–360°
    // Swap photo silently at the start of each cycle while back faces viewer
    card.style.transition = 'none'; // override CSS transition — GSAP owns this
    gsap.to(card, {
      rotationY: '+=360',
      duration: 5,
      ease: 'none',
      repeat: -1,
      onRepeat: function () {
        // Back is facing – load next photo quietly
        img.src = nextPhoto();
      },
    });
  })();
});

