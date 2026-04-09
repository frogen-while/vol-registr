/**
 * Panel JS — extracted inline scripts for the admin panel.
 *
 * Each module is guarded by element existence checks so
 * this single file can be loaded on every panel page.
 */

/* ── Sidebar toggle (mobile) ────────────────────────── */

(function () {
  const sidebar = document.getElementById('pnlSidebar');
  const toggle = document.getElementById('sidebarToggle');
  const close = document.getElementById('sidebarClose');
  if (toggle) toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  if (close) close.addEventListener('click', () => sidebar.classList.remove('open'));
})();

/* ── Batch select (teams list) ──────────────────────── */

(function () {
  const selectAll = document.getElementById('selectAll');
  const batchBar = document.getElementById('batchBar');
  const batchCount = document.getElementById('batchCount');
  if (!selectAll) return;
  const checks = () => document.querySelectorAll('.team-check');

  function update() {
    const all = checks();
    const checked = [...all].filter(c => c.checked).length;
    batchCount.textContent = checked;
    batchBar.style.display = checked > 0 ? 'flex' : 'none';
    selectAll.checked = checked === all.length && all.length > 0;
    selectAll.indeterminate = checked > 0 && checked < all.length;
  }

  selectAll.addEventListener('change', function () {
    checks().forEach(c => c.checked = this.checked);
    update();
  });
  const table = document.querySelector('.pnl-table');
  if (table) {
    table.addEventListener('change', function (e) {
      if (e.target.classList.contains('team-check')) update();
    });
  }
})();

/* ── Dynamic player formset ("Add Player") ──────────── */

(function () {
  const container = document.getElementById('player-forms');
  const addBtn = document.getElementById('add-player');
  const totalInput = document.querySelector('[name="players-TOTAL_FORMS"]');
  if (!container || !addBtn || !totalInput) return;

  addBtn.addEventListener('click', function () {
    const idx = parseInt(totalInput.value, 10);
    const tpl = container.querySelector('.pnl-player-row');
    if (!tpl) return;
    const clone = tpl.cloneNode(true);
    clone.dataset.index = idx;
    clone.classList.remove('pnl-player-row--error');

    clone.querySelectorAll('input, select, textarea').forEach(function (el) {
      if (el.name) el.name = el.name.replace(/-\d+-/, '-' + idx + '-');
      if (el.id) el.id = el.id.replace(/-\d+-/, '-' + idx + '-');
      if (el.type === 'checkbox') el.checked = false;
      else el.value = '';
    });
    clone.querySelectorAll('label[for]').forEach(function (el) {
      el.setAttribute('for', el.getAttribute('for').replace(/-\d+-/, '-' + idx + '-'));
    });
    const idField = clone.querySelector('[name$="-id"]');
    if (idField) idField.value = '';
    const delWrap = clone.querySelector('.pnl-delete-check');
    if (delWrap) delWrap.remove();
    clone.querySelectorAll('.pnl-field__error').forEach(function (el) { el.remove(); });

    container.appendChild(clone);
    totalInput.value = idx + 1;
  });
})();

/* ── Show/hide group field (match form) ─────────────── */

(function () {
  const stageSelect = document.getElementById('id_stage');
  const groupField = document.getElementById('field-group');
  if (!stageSelect || !groupField) return;

  function toggle() {
    groupField.style.display = stageSelect.value === 'GROUP' ? '' : 'none';
  }
  stageSelect.addEventListener('change', toggle);
  toggle();
})();

/* ── Drawer open / close ────────────────────────────── */

(function () {
  const overlay = document.querySelector('.pnl-drawer-overlay');
  const drawer = document.querySelector('.pnl-drawer');
  if (!overlay || !drawer) return;

  document.querySelectorAll('[data-drawer-open]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      overlay.classList.add('open');
      drawer.classList.add('open');
    });
  });

  function closeDrawer() {
    overlay.classList.remove('open');
    drawer.classList.remove('open');
  }

  overlay.addEventListener('click', closeDrawer);
  drawer.querySelectorAll('.pnl-drawer__close').forEach(function (btn) {
    btn.addEventListener('click', closeDrawer);
  });
})();

/* ── AJAX Team Drawer ───────────────────────────────── */

(function () {
  function initAjaxDrawer(containerSelector, overlayId, drawerId, bodyId) {
    var container = document.querySelector(containerSelector);
    if (!container) return;
    var overlay = document.getElementById(overlayId);
    var drawer = document.getElementById(drawerId);
    var body = document.getElementById(bodyId);
    if (!overlay || !drawer || !body) return;

    function openDrawer() {
      overlay.classList.add('open');
      drawer.classList.add('open');
    }

    function closeDrawer() {
      overlay.classList.remove('open');
      drawer.classList.remove('open');
    }

    overlay.addEventListener('click', closeDrawer);
    drawer.querySelectorAll('.pnl-drawer__close').forEach(function (btn) {
      btn.addEventListener('click', closeDrawer);
    });

    container.addEventListener('click', function (e) {
      var link = e.target.closest('[data-drawer-url]');
      if (!link) return;
      e.preventDefault();
      var url = link.getAttribute('data-drawer-url');
      if (!url) return;
      body.innerHTML = '<p style="padding:1rem;color:var(--pnl-muted)">Loading…</p>';
      openDrawer();
      fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) { return r.json(); })
        .then(function (data) { body.innerHTML = data.html; })
        .catch(function () { body.innerHTML = '<p style="padding:1rem;color:#e74c3c">Error loading data.</p>'; });
    });
  }

  // Teams list drawer
  initAjaxDrawer('.pnl-table', 'teamDrawerOverlay', 'teamDrawer', 'teamDrawerBody');
  // Pipeline drawer
  initAjaxDrawer('.pnl-pipeline', 'pipeDrawerOverlay', 'pipeDrawer', 'pipeDrawerBody');
})();

/* ── Pipeline move buttons ──────────────────────────── */

(function () {
  var board = document.querySelector('.pnl-pipeline');
  if (!board) return;
  var csrfToken = '';
  var csrfMeta = document.querySelector('[name=csrfmiddlewaretoken]');
  if (csrfMeta) csrfToken = csrfMeta.value;
  if (!csrfToken) {
    var csrfCookie = document.cookie.split(';').find(function (c) { return c.trim().startsWith('csrftoken='); });
    if (csrfCookie) csrfToken = csrfCookie.split('=')[1];
  }

  board.addEventListener('click', function (e) {
    var btn = e.target.closest('.pnl-pipe-move');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    var url = btn.getAttribute('data-url');
    var newStatus = btn.getAttribute('data-to');
    if (!url || !newStatus) return;
    btn.disabled = true;
    btn.textContent = '…';

    var formData = new FormData();
    formData.append('new_status', newStatus);

    fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      body: formData
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.ok) {
        window.location.reload();
      } else {
        alert(data.error || 'Move failed');
        btn.disabled = false;
        btn.textContent = '→';
      }
    })
    .catch(function () {
      alert('Network error');
      btn.disabled = false;
      btn.textContent = '→';
    });
  });
})();

/* ── Check-in desk — toggle, search, arrival card ───── */

(function () {
  var checkinPage = document.querySelector('.pnl-checkin');
  if (!checkinPage) return;

  var csrfToken = '';
  var csrfMeta = document.querySelector('[name=csrfmiddlewaretoken]');
  if (csrfMeta) csrfToken = csrfMeta.value;
  if (!csrfToken) {
    var csrfCookie = document.cookie.split(';').find(function (c) { return c.trim().startsWith('csrftoken='); });
    if (csrfCookie) csrfToken = csrfCookie.split('=')[1];
  }

  var progressFill = document.getElementById('progressFill');
  var progressText = document.getElementById('progressText');

  function updateProgress(checked, total) {
    var pct = total > 0 ? Math.round((checked / total) * 100) : 0;
    if (progressFill) progressFill.style.width = pct + '%';
    if (progressText) progressText.textContent = checked + ' / ' + total;
  }

  /* Toggle check-in on card */
  checkinPage.addEventListener('change', function (e) {
    var inp = e.target.closest('.pnl-toggle__input');
    if (!inp) return;
    var pk = inp.dataset.pk;
    var card = document.getElementById('card-' + pk);
    fetch(inp.dataset.url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' }
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.ok) {
        inp.checked = data.checked_in;
        if (card) {
          card.classList.toggle('pnl-checkin__card--checked', data.checked_in);
        }
        updateProgress(data.checked, data.total);
      }
    })
    .catch(function () { inp.checked = !inp.checked; });
  });

  /* Instant search */
  var searchInput = document.getElementById('checkinSearch');
  var searchResults = document.getElementById('checkinSearchResults');
  var searchTimer = null;

  if (searchInput && searchResults) {
    searchInput.addEventListener('input', function () {
      clearTimeout(searchTimer);
      var q = searchInput.value.trim();
      if (q.length < 1) {
        searchResults.style.display = 'none';
        return;
      }
      searchTimer = setTimeout(function () {
        var url = searchInput.dataset.url + '?q=' + encodeURIComponent(q);
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (!data.results || data.results.length === 0) {
              searchResults.innerHTML = '<div class="pnl-checkin__search-empty">No teams found</div>';
            } else {
              var html = '';
              data.results.forEach(function (t) {
                var badge = t.checked_in
                  ? '<span class="pnl-checkin__search-item-badge pnl-checkin__search-item-badge--checked">Checked in</span>'
                  : '';
                html += '<div class="pnl-checkin__search-item" data-team=\'' + JSON.stringify(t) + '\'>'
                  + '<div><span class="pnl-checkin__search-item-name">' + t.name + '</span>'
                  + ' <span class="pnl-checkin__search-item-meta">Group ' + t.group + ' · ' + t.captain + '</span></div>'
                  + badge + '</div>';
              });
              searchResults.innerHTML = html;
            }
            searchResults.style.display = '';
          })
          .catch(function () { searchResults.style.display = 'none'; });
      }, 200);
    });

    /* Close search on outside click */
    document.addEventListener('click', function (e) {
      if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.style.display = 'none';
      }
    });

    /* Select search result → open arrival card */
    searchResults.addEventListener('click', function (e) {
      var item = e.target.closest('.pnl-checkin__search-item');
      if (!item) return;
      var team = JSON.parse(item.dataset.team);
      openArrivalCard(team);
      searchResults.style.display = 'none';
      searchInput.value = '';
    });
  }

  /* Arrival card */
  var arrivalCard = document.getElementById('arrivalCard');
  var arrivalClose = document.getElementById('arrivalClose');
  var currentTeam = null;

  function openArrivalCard(team) {
    if (!arrivalCard) return;
    currentTeam = team;
    document.getElementById('arrivalName').textContent = team.name;

    var statusEl = document.getElementById('arrivalStatus');
    if (team.checked_in) {
      statusEl.textContent = 'Checked In';
      statusEl.className = 'pnl-arrival__status pnl-arrival__status--checked';
    } else {
      statusEl.textContent = 'Not Checked In';
      statusEl.className = 'pnl-arrival__status pnl-arrival__status--pending';
    }

    document.getElementById('arrivalCaptain').textContent = team.captain;
    document.getElementById('arrivalPhone').textContent = team.cap_phone || '—';
    document.getElementById('arrivalGroup').textContent = team.group;
    document.getElementById('arrivalRoster').textContent = team.player_count + ' players';
    document.getElementById('arrivalPayment').textContent = team.is_payment_ok ? 'Verified' : 'Pending';

    /* Readiness dots */
    var readHTML = '';
    var checks = [
      { ok: team.is_payment_ok, label: 'Payment' },
      { ok: team.is_roster_complete, label: 'Roster' },
      { ok: team.is_contacts_complete, label: 'Contacts' },
      { ok: team.is_logo_uploaded, label: 'Logo' },
      { ok: !team.has_duplicate_jerseys, label: 'Jerseys' }
    ];
    checks.forEach(function (c) {
      var color = c.ok ? 'var(--pnl-green)' : 'var(--pnl-red,#ef4444)';
      var icon = c.ok ? 'check' : 'times';
      readHTML += '<i class="fas fa-' + icon + '-circle" style="color:' + color + '" title="' + c.label + '"></i> ';
    });
    readHTML += '<span style="margin-left:auto;color:var(--pnl-muted)">' + team.readiness_score + '/5</span>';
    document.getElementById('arrivalReadiness').innerHTML = readHTML;

    /* Issues */
    var issues = [];
    if (!team.is_payment_ok) issues.push('Payment not verified');
    if (!team.is_roster_complete) issues.push('Roster incomplete (' + team.player_count + ' players)');
    if (!team.is_contacts_complete) issues.push('Captain contacts incomplete');
    if (!team.is_logo_uploaded) issues.push('No team logo');
    if (team.has_duplicate_jerseys) issues.push('Duplicate jersey numbers');

    var issuesEl = document.getElementById('arrivalIssues');
    var issuesList = document.getElementById('arrivalIssuesList');
    if (issues.length > 0) {
      issuesList.innerHTML = issues.map(function (i) { return '<li>' + i + '</li>'; }).join('');
      issuesEl.style.display = '';
    } else {
      issuesEl.style.display = 'none';
    }

    /* Update button states */
    var btnComplete = document.getElementById('arrivalBtnComplete');
    if (team.checked_in) {
      btnComplete.innerHTML = '<i class="fas fa-undo"></i> Undo Check-in';
    } else {
      btnComplete.innerHTML = '<i class="fas fa-check"></i> Complete';
    }

    arrivalCard.style.display = '';
    arrivalCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  if (arrivalClose) {
    arrivalClose.addEventListener('click', function () {
      arrivalCard.style.display = 'none';
      currentTeam = null;
    });
  }

  /* Arrival action buttons */
  if (arrivalCard) {
    arrivalCard.addEventListener('click', function (e) {
      var btn = e.target.closest('.pnl-arrival__action');
      if (!btn || !currentTeam) return;
      var action = btn.dataset.action;

      if (action === 'complete') {
        /* Toggle check-in via existing endpoint */
        fetch(currentTeam.toggle_url, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            currentTeam.checked_in = data.checked_in;
            openArrivalCard(currentTeam);
            updateProgress(data.checked, data.total);
            /* Update card in grid */
            var card = document.getElementById('card-' + currentTeam.pk);
            if (card) {
              card.classList.toggle('pnl-checkin__card--checked', data.checked_in);
              var toggle = card.querySelector('.pnl-toggle__input');
              if (toggle) toggle.checked = data.checked_in;
            }
          }
        });
      }
      /* Other actions show visual feedback */
      if (action === 'payment' || action === 'roster' || action === 'waiting') {
        btn.style.outline = '2px solid var(--pnl-accent)';
        setTimeout(function () { btn.style.outline = ''; }, 1500);
      }
    });
  }
})();

/* ================================================================
   6. Match Quick-Panel (drawer)
   ================================================================ */
(function () {
  var overlay = document.getElementById('matchDrawerOverlay');
  var drawer  = document.getElementById('matchDrawer');
  var body    = document.getElementById('matchDrawerBody');
  if (!overlay || !drawer || !body) return;

  var csrfToken = (document.querySelector('[name=csrfmiddlewaretoken]') ||
                   document.querySelector('meta[name="csrf-token"]') || {}).value ||
                  (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';

  function openMatchDrawer() {
    overlay.classList.add('pnl-drawer-overlay--open');
    drawer.classList.add('pnl-drawer--open');
  }
  function closeMatchDrawer() {
    overlay.classList.remove('pnl-drawer-overlay--open');
    drawer.classList.remove('pnl-drawer--open');
    body.innerHTML = '';
  }
  overlay.addEventListener('click', closeMatchDrawer);
  drawer.querySelector('.pnl-drawer__close').addEventListener('click', closeMatchDrawer);

  /* Load panel via AJAX */
  function loadMatchPanel(url) {
    body.innerHTML = '<p class="pnl-muted" style="padding:2rem;">Loading…</p>';
    openMatchDrawer();
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (data) { body.innerHTML = data.html; })
      .catch(function () { body.innerHTML = '<p class="pnl-muted">Error loading panel.</p>'; });
  }

  /* Click on match link (table or grid) */
  document.addEventListener('click', function (e) {
    var link = e.target.closest('.pnl-match-panel-link');
    if (link) { e.preventDefault(); loadMatchPanel(link.dataset.panelUrl); return; }

    var cell = e.target.closest('.pnl-grid-schedule__cell[data-panel-url]');
    if (cell && !e.target.closest('a')) { loadMatchPanel(cell.dataset.panelUrl); return; }
  });

  /* Delegated handlers inside drawer body */
  body.addEventListener('click', function (e) {
    /* Score save */
    var saveBtn = e.target.closest('.pnl-mp__score-save');
    if (saveBtn) {
      var url = saveBtn.dataset.url;
      var scoreA = body.querySelector('#mpScoreA');
      var scoreB = body.querySelector('#mpScoreB');
      if (!scoreA || !scoreB) return;
      var fd = new FormData();
      fd.append('score_a', scoreA.value);
      fd.append('score_b', scoreB.value);
      fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrfToken }, body: fd })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            saveBtn.textContent = '✓ Saved';
            setTimeout(function () { saveBtn.textContent = 'Save'; }, 1500);
          }
        });
      return;
    }

    /* Status change */
    var statusBtn = e.target.closest('.pnl-mp__status-btn');
    if (statusBtn) {
      var sUrl = statusBtn.dataset.url;
      var newStatus = statusBtn.dataset.to;
      var sd = new FormData();
      sd.append('new_status', newStatus);
      fetch(sUrl, { method: 'POST', headers: { 'X-CSRFToken': csrfToken }, body: sd })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            /* Re-load panel to reflect new status */
            var panelUrl = sUrl.replace('/status/', '/panel/');
            loadMatchPanel(panelUrl);
          }
        });
      return;
    }
  });
})();

/* ── Command Palette (Ctrl+K / Cmd+K) ──────────────── */

(function () {
  var overlay = document.getElementById('cmdPalette');
  var backdrop = document.getElementById('cmdBackdrop');
  var input = document.getElementById('cmdInput');
  var resultsList = document.getElementById('cmdResults');
  if (!overlay || !input || !resultsList) return;

  var activeIdx = -1;
  var items = [];
  var searchTimer = null;

  function open() {
    overlay.style.display = '';
    input.value = '';
    resultsList.innerHTML = '';
    activeIdx = -1;
    items = [];
    input.focus();
    doSearch('');
  }

  function close() {
    overlay.style.display = 'none';
    input.value = '';
    resultsList.innerHTML = '';
    activeIdx = -1;
    items = [];
  }

  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      if (overlay.style.display === 'none') open();
      else close();
    }
    if (e.key === 'Escape' && overlay.style.display !== 'none') {
      close();
    }
  });

  if (backdrop) backdrop.addEventListener('click', close);

  function doSearch(q) {
    fetch('/panel/cmd-search/?q=' + encodeURIComponent(q), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      renderResults(data.results || []);
    })
    .catch(function () {
      resultsList.innerHTML = '<li class="pnl-cmd-empty">Search unavailable</li>';
    });
  }

  function renderResults(results) {
    items = results;
    activeIdx = -1;
    if (results.length === 0) {
      resultsList.innerHTML = '<li class="pnl-cmd-empty">No results found</li>';
      return;
    }
    var html = '';
    results.forEach(function (r, i) {
      var typeClass = 'pnl-cmd-type--' + r.type;
      html += '<li class="pnl-cmd-item" data-idx="' + i + '" data-url="' + r.url + '">'
        + '<i class="fas ' + r.icon + ' pnl-cmd-item__icon"></i>'
        + '<span class="pnl-cmd-item__label">' + r.label + '</span>'
        + '<span class="pnl-cmd-item__type ' + typeClass + '">' + r.type + '</span>'
        + '</li>';
    });
    resultsList.innerHTML = html;
  }

  function highlightIdx(idx) {
    var allLis = resultsList.querySelectorAll('.pnl-cmd-item');
    allLis.forEach(function (li) { li.classList.remove('pnl-cmd-item--active'); });
    if (idx >= 0 && idx < allLis.length) {
      allLis[idx].classList.add('pnl-cmd-item--active');
      allLis[idx].scrollIntoView({ block: 'nearest' });
    }
  }

  function navigate(url) {
    close();
    window.location.href = url;
  }

  input.addEventListener('input', function () {
    clearTimeout(searchTimer);
    var q = input.value.trim();
    searchTimer = setTimeout(function () { doSearch(q); }, 180);
  });

  input.addEventListener('keydown', function (e) {
    var total = items.length;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeIdx = (activeIdx + 1) % total;
      highlightIdx(activeIdx);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeIdx = (activeIdx - 1 + total) % total;
      highlightIdx(activeIdx);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIdx >= 0 && activeIdx < total) {
        navigate(items[activeIdx].url);
      }
    }
  });

  resultsList.addEventListener('click', function (e) {
    var li = e.target.closest('.pnl-cmd-item');
    if (li) navigate(li.dataset.url);
  });
})();
