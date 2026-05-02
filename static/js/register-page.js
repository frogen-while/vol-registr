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
  let activeLogoFile = null;

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

  function animatePanelDetails(panel) {
    if (!panel) return;
    const items = panel.querySelectorAll('.reg-panel__title, .reg-panel__hint, .reg-panel__note, .reg-field, .roster-row, .reg-btn, .reg-logo-upload, .reg-check');
    if (!items.length) return;

    gsap.killTweensOf(items);
    gsap.fromTo(items,
      { opacity: 0, y: 18 },
      {
        opacity: 1,
        y: 0,
        duration: 0.45,
        stagger: 0.05,
        ease: 'power2.out',
        clearProps: 'opacity,transform',
      },
    );
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
      {
        opacity: 1,
        x: 0,
        duration: 0.35,
        ease: 'power2.out',
        delay: 0.2,
        onComplete: () => animatePanelDetails(nextPanel),
      },
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
    clearErrors('teamName', 'capName', 'phone', 'email', 'logo');
    let ok = true;

    const teamName = document.getElementById('teamName');
    if (!teamName.value.trim()) {
      setError('teamName', '', 'err_team_name');
      markInputError(teamName, true);
      ok = false;
    } else {
      markInputError(teamName, false);
    }

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

    if (activeLogoFile) {
      if (!/^image\/(png|jpeg|webp)$/i.test(activeLogoFile.type)) {
        setError('logo', '', 'err_logo_type');
        ok = false;
      } else if (activeLogoFile.size > 5 * 1024 * 1024) {
        setError('logo', '', 'err_logo_size');
        ok = false;
      }
    }

    return ok;
  }

  // -- Step 2 Validation --
  function validateStep2() {
    clearErrors('logo');
    let ok = true;

    if (activeLogoFile) {
      if (!/^image\/(png|jpeg|webp)$/i.test(activeLogoFile.type)) {
        setError('logo', '', 'err_logo_type');
        ok = false;
      } else if (activeLogoFile.size > 5 * 1024 * 1024) {
        setError('logo', '', 'err_logo_size');
        ok = false;
      }
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
      const validators = {
        1: validateStep1,
        2: validateStep2,
      };

      if (validators[currentStep] && !validators[currentStep]()) return;

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
          '<input class="reg-input roster-first" type="text" placeholder="First Name" maxlength="50" data-i18n-ph="reg_first">' +
          '<input class="reg-input roster-last" type="text" placeholder="Last Name" maxlength="50" data-i18n-ph="reg_last">' +
        '</div>';

      rosterList.appendChild(row);
      applyLangReg(lang);

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

      if (first && last) {
        players.push({
          firstName:    first,
          lastName:     last,
        });
      }
    });
    return players;
  }

  const logoInput = document.getElementById('teamLogo');
  const logoDropzone = document.getElementById('logoDropzone');
  const logoPreview = document.getElementById('logoPreview');
  const logoPreviewImage = document.getElementById('logoPreviewImage');
  const logoPreviewIcon = document.getElementById('logoPreviewIcon');
  const logoFileName = document.getElementById('logoFileName');
  const removeLogoBtn = document.getElementById('removeLogoBtn');

  function clearLogoPreview() {
    activeLogoFile = null;
    if (logoInput) logoInput.value = '';
    if (logoPreview) logoPreview.classList.add('reg-logo-hidden');
    if (logoPreviewImage) {
      logoPreviewImage.src = '';
      logoPreviewImage.classList.add('reg-logo-hidden');
    }
    if (logoPreviewIcon) logoPreviewIcon.classList.remove('reg-logo-hidden');
    if (logoFileName) logoFileName.textContent = '';
    clearErrors('logo');
  }

  function showLogoPreview(file) {
    if (!file) {
      clearLogoPreview();
      return;
    }

    activeLogoFile = file;
    if (logoPreview) logoPreview.classList.remove('reg-logo-hidden');
    if (logoFileName) logoFileName.textContent = file.name;
    if (logoPreview) {
      gsap.fromTo(logoPreview,
        { opacity: 0, y: 10 },
        { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out', clearProps: 'opacity,transform' },
      );
    }
    if (!logoPreviewImage) return;

    const reader = new FileReader();
    reader.onload = event => {
      logoPreviewImage.src = event.target.result;
      logoPreviewImage.classList.remove('reg-logo-hidden');
      if (logoPreviewIcon) logoPreviewIcon.classList.add('reg-logo-hidden');
    };
    reader.readAsDataURL(file);
  }

  if (logoInput) {
    logoInput.addEventListener('change', event => {
      const file = event.target.files && event.target.files[0];
      if (!file) {
        clearLogoPreview();
        return;
      }
      showLogoPreview(file);
    });
  }

  if (removeLogoBtn) {
    removeLogoBtn.addEventListener('click', clearLogoPreview);
  }

  // -- Entrance Song (SoundCloud Search + Crop Modal) --
  let scWidget = null;
  let trackDurationMs = 0;
  let currentStartSeconds = 0;
  let isDraggingCrop = false;
  let dragOffsetX = 0;
  let isScPlaying = false;
  let currentSoundResult = null;
  const waveformCache = new Map();

  const openScModalBtn = document.getElementById('openScModalBtn');
  const scCropModal = document.getElementById('scCropModal');
  const closeScModalBtn = document.getElementById('closeScModalBtn');
  const scErrorMsg = document.getElementById('scErrorMsg');
  const scLoading = document.getElementById('scLoading');
  const scEditorArea = document.getElementById('scEditorArea');
  const scTrackLink = document.getElementById('scTrackLink');
  const scArtistLink = document.getElementById('scArtistLink');
  const scPseudoWaveform = document.getElementById('scPseudoWaveform');
  const scCropper = document.getElementById('scCropper');
  const scCropperTime = document.getElementById('scCropperTime');
  const scWaveformContainer = document.getElementById('scWaveformContainer');
  const scPlayPreviewBtn = document.getElementById('scPlayPreviewBtn');
  const scConfirmBtn = document.getElementById('scConfirmBtn');
  const scHiddenWidget = document.getElementById('scHiddenWidget');
  const scProgressFill = document.getElementById('scProgressFill');
  const scProgressHead = document.getElementById('scProgressHead');
  const scPreviewProgressLabel = document.getElementById('scPreviewProgressLabel');

  const entranceSongChooseBlock = document.getElementById('entranceSongChooseBlock');
  const entranceSongSelectedBlock = document.getElementById('entranceSongSelectedBlock');
  const finalSongArtwork = document.getElementById('finalSongArtwork');
  const finalSongTitle = document.getElementById('finalSongTitle');
  const finalSongArtist = document.getElementById('finalSongArtist');
  const finalSongStart = document.getElementById('finalSongStart');
  const removeScSongBtn = document.getElementById('removeScSongBtn');

  const scSearchInput = document.getElementById('scSearchInput');
  const scSearchBtn = document.getElementById('scSearchBtn');
  const scSearchStatus = document.getElementById('scSearchStatus');
  const scSearchResults = document.getElementById('scSearchResults');

  const entranceUrlInput = document.getElementById('entranceUrl');
  const entranceTitleInput = document.getElementById('entranceTitle');
  const entranceArtistInput = document.getElementById('entranceArtist');
  const entranceArtworkUrlInput = document.getElementById('entranceArtworkUrl');
  const entranceSourceInput = document.getElementById('entranceSource');
  const entranceStartSecondsInput = document.getElementById('entranceStartSeconds');

  const clipLengthSeconds = 15;

  let scScriptLoadPromise = null;
  let scWidgetInitPromise = null;

  function ensureScScript() {
    if (window.SC && typeof window.SC.Widget === 'function') {
      return Promise.resolve();
    }

    if (scScriptLoadPromise) {
      return scScriptLoadPromise;
    }

    scScriptLoadPromise = new Promise((resolve, reject) => {
      const existingScript = document.querySelector('script[src="https://w.soundcloud.com/player/api.js"]');

      const handleLoad = () => resolve();
      const handleError = () => reject(new Error('SoundCloud player API failed to load'));

      if (existingScript) {
        existingScript.addEventListener('load', handleLoad, { once: true });
        existingScript.addEventListener('error', handleError, { once: true });
        window.setTimeout(() => {
          if (window.SC && typeof window.SC.Widget === 'function') {
            resolve();
          }
        }, 0);
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://w.soundcloud.com/player/api.js';
      script.async = true;
      script.addEventListener('load', handleLoad, { once: true });
      script.addEventListener('error', handleError, { once: true });
      document.head.appendChild(script);
    }).catch((error) => {
      scScriptLoadPromise = null;
      throw error;
    });

    return scScriptLoadPromise;
  }

  function initScWidget() {
    if (scWidget || !scHiddenWidget) return scWidget;
    if (!window.SC || typeof window.SC.Widget !== 'function') return null;

    try {
      scWidget = window.SC.Widget(scHiddenWidget);
      return scWidget;
    } catch (error) {
      return null;
    }
  }

  function ensureScWidget() {
    const readyWidget = initScWidget();
    if (readyWidget) return Promise.resolve(readyWidget);
    if (scWidgetInitPromise) return scWidgetInitPromise;

    scWidgetInitPromise = ensureScScript()
      .catch(() => null)
      .then(() => new Promise((resolve) => {
        let attempts = 0;
        const maxAttempts = 20;

        const tryInit = () => {
          const widget = initScWidget();
          if (widget) {
            resolve(widget);
            return;
          }

          attempts += 1;
          if (attempts >= maxAttempts) {
            resolve(null);
            return;
          }

          window.setTimeout(tryInit, 250);
        };

        tryInit();
      }))
      .finally(() => {
        scWidgetInitPromise = null;
      });

    return scWidgetInitPromise;
  }

  function formatTime(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = String(Math.floor(totalSeconds % 60)).padStart(2, '0');
    return `${minutes}:${seconds}`;
  }

  function setScError(message) {
    if (!scErrorMsg) return;
    scErrorMsg.textContent = message || '';
    scErrorMsg.style.display = message ? 'block' : 'none';
  }

  function setSearchStatus(message) {
    if (!scSearchStatus) return;
    scSearchStatus.textContent = message || '';
    scSearchStatus.style.display = message ? 'block' : 'none';
  }

  function resetPreviewButton() {
    if (scPlayPreviewBtn) {
      scPlayPreviewBtn.innerHTML = '<i class="fas fa-play" style="margin-left: 3px;"></i>';
    }
  }

  function updatePreviewProgress(progressMs = 0) {
    const clipMs = clipLengthSeconds * 1000;
    const clamped = Math.max(0, Math.min(progressMs, clipMs));
    const ratio = clipMs ? (clamped / clipMs) : 0;

    if (scProgressFill) scProgressFill.style.width = `${ratio * 100}%`;
    if (scProgressHead) scProgressHead.style.left = `${ratio * 100}%`;
    if (scPreviewProgressLabel) {
      scPreviewProgressLabel.textContent = `Preview progress: ${formatTime(clamped / 1000)} / ${formatTime(clipLengthSeconds)}`;
    }
  }

  function stopScPreview() {
    if (scWidget) scWidget.pause();
    resetPreviewButton();
    updatePreviewProgress(0);
  }

  function stopCropDrag() {
    if (!isDraggingCrop) return;
    isDraggingCrop = false;
    if (scCropper) scCropper.style.cursor = 'grab';
  }

  function openScModal() {
    if (!scCropModal) return;
    scCropModal.style.display = 'flex';
    setScError('');
    void ensureScWidget();
    if (scSearchInput) scSearchInput.focus();
  }

  function closeScModal() {
    if (!scCropModal) return;
    scCropModal.style.display = 'none';
    stopScPreview();
    stopCropDrag();
  }

  function downsampleSamples(samples, targetCount = 96) {
    if (!samples.length) return [];

    const bucketSize = samples.length / targetCount;
    const bars = [];

    for (let index = 0; index < targetCount; index += 1) {
      const start = Math.floor(index * bucketSize);
      const end = Math.max(start + 1, Math.floor((index + 1) * bucketSize));
      let bucketMax = 0;

      for (let cursor = start; cursor < end && cursor < samples.length; cursor += 1) {
        bucketMax = Math.max(bucketMax, samples[cursor]);
      }

      bars.push(bucketMax);
    }

    return bars;
  }

  function renderWaveform(samples) {
    if (!scPseudoWaveform) return;
    scPseudoWaveform.innerHTML = '';

    const bars = downsampleSamples(samples);
    const maxSample = Math.max(...bars, 1);

    bars.forEach((sample) => {
      const bar = document.createElement('div');
      const barHeight = Math.max(12, Math.round((sample / maxSample) * 100));
      bar.style.width = '3px';
      bar.style.height = `${barHeight}%`;
      bar.style.background = 'linear-gradient(180deg, rgba(255,255,255,0.88), rgba(255,255,255,0.18))';
      bar.style.borderRadius = '999px';
      bar.style.flex = '0 0 auto';
      scPseudoWaveform.appendChild(bar);
    });
  }

  async function fetchWaveformSamples(waveformUrl) {
    if (!waveformUrl) return [];
    if (waveformCache.has(waveformUrl)) return waveformCache.get(waveformUrl);

    const response = await fetch(waveformUrl, { mode: 'cors' });
    if (!response.ok) {
      throw new Error('Waveform request failed');
    }

    const payload = await response.json();
    const samples = Array.isArray(payload.samples) ? payload.samples : [];
    waveformCache.set(waveformUrl, samples);
    return samples;
  }

  function updateCropperPosition() {
    if (!scCropper || !scWaveformContainer || !scCropperTime || !trackDurationMs) return;

    const durationSeconds = trackDurationMs / 1000;
    const clipRatio = Math.min(clipLengthSeconds / durationSeconds, 1);
    const containerWidth = scWaveformContainer.clientWidth;
    const cropperWidth = Math.max(containerWidth * clipRatio, Math.min(containerWidth, 56));
    const maxStart = Math.max(durationSeconds - clipLengthSeconds, 0);
    currentStartSeconds = Math.min(currentStartSeconds, maxStart);
    const leftPx = maxStart > 0 ? (currentStartSeconds / maxStart) * (containerWidth - cropperWidth) : 0;

    scCropper.style.width = `${cropperWidth}px`;
    scCropper.style.left = `${leftPx}px`;
    scCropperTime.textContent = formatTime(currentStartSeconds);
  }

  function resolveStartFromPointer(clientX) {
    if (!scWaveformContainer || !scCropper || !trackDurationMs) return;

    const rect = scWaveformContainer.getBoundingClientRect();
    const cropperWidth = scCropper.offsetWidth;
    const durationSeconds = trackDurationMs / 1000;
    const maxStart = Math.max(durationSeconds - clipLengthSeconds, 0);
    
    let leftPx = clientX - rect.left - dragOffsetX;
    leftPx = Math.max(0, Math.min(leftPx, rect.width - cropperWidth));

    currentStartSeconds = maxStart > 0 ? (leftPx / Math.max(rect.width - cropperWidth, 1)) * maxStart : 0;
    updateCropperPosition();
    updatePreviewProgress(0);

    if (isScPlaying && scWidget) {
      scWidget.seekTo(currentStartSeconds * 1000);
    }
  }

  function populateSelectedSongCard() {
    const artwork = currentSoundResult?.artwork_url || '';
    const title = currentSoundResult?.title || '';
    const artist = currentSoundResult?.artist || '';
    const url = currentSoundResult?.url || '#';

    if (finalSongArtwork) {
      finalSongArtwork.src = artwork;
      finalSongArtwork.style.display = artwork ? 'block' : 'none';
    }

    if (finalSongTitle) {
      finalSongTitle.textContent = title;
      finalSongTitle.href = url;
    }

    if (finalSongArtist) {
      finalSongArtist.textContent = artist;
      finalSongArtist.style.display = artist ? 'block' : 'none';
    }

    if (finalSongStart) {
      finalSongStart.textContent = `Starts at ${formatTime(currentStartSeconds)}`;
    }

    if (entranceSongChooseBlock) entranceSongChooseBlock.style.display = 'none';
    if (entranceSongSelectedBlock) entranceSongSelectedBlock.style.display = 'block';
  }

  async function loadSearchResult(result) {
    currentSoundResult = result;
    trackDurationMs = result.duration_ms || 0;
    currentStartSeconds = 0;
    setScError('');
    stopScPreview();
    stopCropDrag();

    if (scTrackLink) {
      scTrackLink.textContent = result.title || 'SoundCloud track';
      scTrackLink.href = result.url || '#';
    }

    if (scArtistLink) {
      scArtistLink.textContent = result.artist || 'SoundCloud artist';
      scArtistLink.href = result.artist_url || result.url || '#';
    }

    if (scLoading) scLoading.style.display = 'block';
    if (scEditorArea) scEditorArea.style.display = 'none';
    setSearchStatus(`Loading ${result.title || 'track'}...`);

    try {
      const samples = await fetchWaveformSamples(result.waveform_url);
      renderWaveform(samples);
      updateCropperPosition();
    } catch (error) {
      setScError('Could not load the waveform for this track.');
      if (scLoading) scLoading.style.display = 'none';
      return;
    }

    const widget = await ensureScWidget();
    if (!widget) {
      setScError('SoundCloud widget is unavailable right now.');
      if (scLoading) scLoading.style.display = 'none';
      return;
    }

    if (window.SC?.Widget?.Events?.READY) {
      widget.unbind(window.SC.Widget.Events.READY);
      widget.unbind(window.SC.Widget.Events.PLAY_PROGRESS);
      widget.unbind(window.SC.Widget.Events.PLAY);
      widget.unbind(window.SC.Widget.Events.PAUSE);
    }

    widget.bind(window.SC.Widget.Events.READY, () => {
      if (scLoading) scLoading.style.display = 'none';
      if (scEditorArea) scEditorArea.style.display = 'block';
      setSearchStatus(`Loaded ${result.title || 'track'}. Drag the 15-second window and preview it on the right.`);
      updateCropperPosition();
      updatePreviewProgress(0);
    });

    widget.bind(window.SC.Widget.Events.PLAY, () => {
      isScPlaying = true;
    });

    widget.bind(window.SC.Widget.Events.PAUSE, () => {
      isScPlaying = false;
      resetPreviewButton();
    });

    widget.bind(window.SC.Widget.Events.PLAY_PROGRESS, (event) => {
      const elapsedMs = Math.max(0, (event?.currentPosition || 0) - (currentStartSeconds * 1000));
      updatePreviewProgress(elapsedMs);
      if (elapsedMs >= clipLengthSeconds * 1000) {
        stopScPreview();
      }
    });

    widget.load(result.url, {
      auto_play: false,
      show_comments: false,
      show_user: false,
      show_reposts: false,
      visual: false,
    });
  }

  function renderSearchResults(results) {
    if (!scSearchResults) return;

    scSearchResults.innerHTML = '';

    if (!results.length) {
      scSearchResults.style.display = 'none';
      setSearchStatus('No SoundCloud tracks found for this query.');
      return;
    }

    setSearchStatus(`Found ${results.length} track${results.length === 1 ? '' : 's'}. Choose the exact track and then trim the 15-second clip.`);
    scSearchResults.style.display = 'block';

    results.forEach((result) => {
      const row = document.createElement('div');
      row.className = 'song-result';

      const artwork = result.artwork_url || '';
      const durationLabel = result.duration_ms ? formatTime(result.duration_ms / 1000) : '';
      row.innerHTML = `
        <img src="${artwork}" alt="Artwork" style="display:${artwork ? 'block' : 'none'};">
        <div class="song-result-info">
          <div class="song-result-title">${result.title || 'Untitled track'}</div>
          <div class="song-result-artist">${result.artist || 'SoundCloud'}${durationLabel ? ` • ${durationLabel}` : ''}</div>
        </div>
        <div class="song-result-actions">
          <button type="button" class="song-btn-use">Select</button>
        </div>
      `;

      const useButton = row.querySelector('.song-btn-use');
      if (useButton) {
        useButton.addEventListener('click', () => {
          loadSearchResult(result);
        });
      }

      scSearchResults.appendChild(row);
    });
  }

  async function searchSoundCloud() {
    const query = scSearchInput?.value.trim() || '';
    setScError('');

    if (!query) {
      setSearchStatus('Enter a track name or artist to search SoundCloud.');
      if (scSearchResults) {
        scSearchResults.innerHTML = '';
        scSearchResults.style.display = 'none';
      }
      return;
    }

    setSearchStatus('Searching SoundCloud...');
    if (scSearchResults) {
      scSearchResults.innerHTML = '';
      scSearchResults.style.display = 'none';
    }

    try {
      const response = await fetch(`/api/soundcloud-search/?q=${encodeURIComponent(query)}`);
      const payload = await response.json();

      if (!response.ok || !payload.success) {
        setSearchStatus(payload.error || 'SoundCloud search is unavailable right now.');
        return;
      }

      renderSearchResults(payload.results || []);
    } catch (error) {
      setSearchStatus('Could not search SoundCloud right now.');
    }
  }

  if (openScModalBtn) openScModalBtn.addEventListener('click', openScModal);
  if (closeScModalBtn) closeScModalBtn.addEventListener('click', closeScModal);

  if (scCropModal) {
    scCropModal.addEventListener('click', (event) => {
      if (event.target === scCropModal) closeScModal();
    });
  }

  if (scSearchBtn) scSearchBtn.addEventListener('click', searchSoundCloud);
  if (scSearchInput) {
    scSearchInput.addEventListener('keypress', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        searchSoundCloud();
      }
    });
  }

  if (scCropper) {
    scCropper.style.touchAction = 'none';

    scCropper.addEventListener('pointerdown', (event) => {
      event.preventDefault();
      isDraggingCrop = true;
      scCropper.style.cursor = 'grabbing';
      
      const cropperRect = scCropper.getBoundingClientRect();
      dragOffsetX = event.clientX - cropperRect.left;

      if (scCropper.setPointerCapture) {
        scCropper.setPointerCapture(event.pointerId);
      }
    });

    scCropper.addEventListener('pointermove', (event) => {
      if (!isDraggingCrop) return;
      resolveStartFromPointer(event.clientX);
    });

    const finishCropDrag = (event) => {
      if (scCropper.hasPointerCapture && scCropper.hasPointerCapture(event.pointerId)) {
        scCropper.releasePointerCapture(event.pointerId);
      }
      stopCropDrag();
    };

    scCropper.addEventListener('pointerup', finishCropDrag);
    scCropper.addEventListener('pointercancel', finishCropDrag);
  }

  window.addEventListener('resize', updateCropperPosition);

  if (scPlayPreviewBtn) {
    scPlayPreviewBtn.addEventListener('click', async () => {
      if (!currentSoundResult) return;

      const widget = await ensureScWidget();
      if (!widget) {
        setScError('SoundCloud widget is unavailable right now.');
        return;
      }

      widget.isPaused((paused) => {
        if (!paused) {
          stopScPreview();
          return;
        }

        widget.seekTo(currentStartSeconds * 1000);
        widget.play();
        scPlayPreviewBtn.innerHTML = '<i class="fas fa-pause"></i>';
        updatePreviewProgress(0);
      });
    });
  }

  if (scConfirmBtn) {
    scConfirmBtn.addEventListener('click', () => {
      if (!currentSoundResult) return;
      if (entranceUrlInput) entranceUrlInput.value = currentSoundResult.url || '';
      if (entranceTitleInput) entranceTitleInput.value = currentSoundResult.title || '';
      if (entranceArtistInput) entranceArtistInput.value = currentSoundResult.artist || '';
      if (entranceArtworkUrlInput) entranceArtworkUrlInput.value = currentSoundResult.artwork_url || '';
      if (entranceSourceInput) entranceSourceInput.value = 'soundcloud';
      if (entranceStartSecondsInput) entranceStartSecondsInput.value = String(Math.floor(currentStartSeconds));

      populateSelectedSongCard();
      closeScModal();
    });
  }

  if (removeScSongBtn) {
    removeScSongBtn.addEventListener('click', () => {
      if (entranceUrlInput) entranceUrlInput.value = '';
      if (entranceTitleInput) entranceTitleInput.value = '';
      if (entranceArtistInput) entranceArtistInput.value = '';
      if (entranceArtworkUrlInput) entranceArtworkUrlInput.value = '';
      if (entranceSourceInput) entranceSourceInput.value = 'soundcloud';
      if (entranceStartSecondsInput) entranceStartSecondsInput.value = '0';
      currentSoundResult = null;

      if (entranceSongChooseBlock) entranceSongChooseBlock.style.display = 'block';
      if (entranceSongSelectedBlock) entranceSongSelectedBlock.style.display = 'none';
    });
  }

  if (logoDropzone) {
    ['dragenter', 'dragover'].forEach(eventName => {
      logoDropzone.addEventListener(eventName, event => {
        event.preventDefault();
        logoDropzone.classList.add('is-dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      logoDropzone.addEventListener(eventName, event => {
        event.preventDefault();
        logoDropzone.classList.remove('is-dragover');
      });
    });

    logoDropzone.addEventListener('drop', event => {
      const files = event.dataTransfer && event.dataTransfer.files;
      const file = files && files[0];
      if (!file) return;
      try {
        const transfer = new DataTransfer();
        transfer.items.add(file);
        if (logoInput) logoInput.files = transfer.files;
      } catch (dropError) {
        // ignore when the browser blocks assigning dropped files
      }
      showLogoPreview(file);
    });
  }

  // -- Form Submit --
  const form       = document.getElementById('registrationForm');
  const submitBtn  = document.getElementById('submitBtn');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!validateStep3()) return;

    const payload = {
      teamName:    document.getElementById('teamName')?.value.trim() || '',
      capName:     document.getElementById('capName')?.value.trim() || '',
      phone:       document.getElementById('phone')?.value.trim() || '',
      email:       document.getElementById('email')?.value.trim() || '',
      entranceUrl: document.getElementById('entranceUrl')?.value.trim() || '',
      entranceTitle: document.getElementById('entranceTitle')?.value.trim() || '',
      entranceArtist: document.getElementById('entranceArtist')?.value.trim() || '',
      entranceArtworkUrl: document.getElementById('entranceArtworkUrl')?.value.trim() || '',
      entranceSource: document.getElementById('entranceSource')?.value.trim() || 'soundcloud',
      entranceStartSeconds: parseInt(document.getElementById('entranceStartSeconds')?.value || 0, 10),
      players:     collectPlayers(),
      lang:        localStorage.getItem('pa_lang') || 'en',
    };
    const formData = new FormData();
    formData.append('teamName', payload.teamName);
    formData.append('capName', payload.capName);
    formData.append('phone', payload.phone);
    formData.append('email', payload.email);
    formData.append('entranceUrl', payload.entranceUrl);
    formData.append('entranceTitle', payload.entranceTitle);
    formData.append('entranceArtist', payload.entranceArtist);
    formData.append('entranceArtworkUrl', payload.entranceArtworkUrl);
    formData.append('entranceSource', payload.entranceSource);
    formData.append('entranceStartSeconds', payload.entranceStartSeconds);
    formData.append('players', JSON.stringify(payload.players));
    formData.append('lang', payload.lang);
    if (activeLogoFile) formData.append('logo', activeLogoFile);

    // Loading state
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    try {
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

      const res = await fetch('/api/register/', {
        method:  'POST',
        headers: {
          'X-CSRFToken':  csrfToken,
        },
        body: formData,
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
        setError('checks', data.error || '', data.error ? null : 'err_failed');
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
  const introTl = gsap.timeline();
  const regHero = document.querySelector('.reg-brand__hero');
  const regAccessPanel = document.querySelector('.reg-layout__access');
  const regFormCol = document.querySelector('.reg-form-col');

  introTl
    .from(regHero, {
      opacity: 0,
      y: 30,
      duration: 0.7,
      ease: 'power2.out',
      delay: 0.1,
    });

  if (regFormCol) {
    introTl.from(regFormCol, {
      opacity: 0,
      x: 28,
      duration: 0.65,
      ease: 'power2.out',
    }, '-=0.45');
  }

  introTl.from('.reg-stepper', {
      opacity: 0,
      y: 18,
      duration: 0.45,
      ease: 'power2.out',
    }, '-=0.45');

  if (regAccessPanel) {
    introTl.from(regAccessPanel, {
      opacity: 0,
      y: 20,
      duration: 0.55,
      ease: 'power2.out',
    }, '-=0.3');
  }

  gsap.delayedCall(0.45, () => animatePanelDetails(panels[1]));

  // Initial stepper state
  updateStepper(1);
});
