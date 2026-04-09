/* ================================================================
   Arena Editorial — Core JS
   Pocket Aces Tournament · Public Entity Pages
   ================================================================ */

(function () {
  'use strict';

  /* ── 1. Reveal Observer ─────────────────────────────────────── */

  function initReveal() {
    var els = document.querySelectorAll('.ae-reveal');
    if (!els.length) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1 }
    );

    els.forEach(function (el) {
      observer.observe(el);
    });
  }

  /* ── 2. Anchor Nav Sync ─────────────────────────────────────── */

  function initAnchorNav() {
    var links = document.querySelectorAll('[data-ae-target]');
    var sections = document.querySelectorAll('[data-ae-section]');
    if (!links.length || !sections.length) return;

    /* Click handler — smooth scroll + update URL */
    links.forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        var targetId = link.getAttribute('data-ae-target');
        var target = document.getElementById(targetId);
        if (!target) return;

        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        history.replaceState(null, '', '#' + targetId);
        setActiveLink(targetId);
      });
    });

    /* IO — auto-track active section on scroll */
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var id = entry.target.getAttribute('id');
            if (id) setActiveLink(id);
          }
        });
      },
      { rootMargin: '-25% 0px -55% 0px', threshold: [0.15, 0.4] }
    );

    sections.forEach(function (sec) {
      observer.observe(sec);
    });

    function setActiveLink(id) {
      links.forEach(function (l) {
        l.classList.toggle('is-active', l.getAttribute('data-ae-target') === id);
      });
    }
  }

  /* ── 3. View Toggle (Team A / Team B / All) ─────────────────── */

  function initViewToggle() {
    var toggles = document.querySelectorAll('[data-ae-view-toggle]');
    if (!toggles.length) return;

    toggles.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var group = btn.getAttribute('data-ae-view-toggle');
        var view = btn.getAttribute('data-ae-view');
        if (!group || !view) return;

        /* Update toggle buttons */
        document
          .querySelectorAll('[data-ae-view-toggle="' + group + '"]')
          .forEach(function (b) {
            b.classList.toggle('is-active', b === btn);
            b.setAttribute('aria-selected', b === btn ? 'true' : 'false');
          });

        /* Update panels */
        document
          .querySelectorAll('[data-ae-view-panel="' + group + '"]')
          .forEach(function (panel) {
            var panelView = panel.getAttribute('data-ae-view');
            panel.classList.toggle('is-hidden', panelView !== view);
          });
      });
    });
  }

  /* ── 4. Table Sorting ───────────────────────────────────────── */

  function initTableSort() {
    var tables = document.querySelectorAll('.ae-table[data-ae-sortable]');

    tables.forEach(function (table) {
      var headers = table.querySelectorAll('th[data-ae-sort-key]');
      headers.forEach(function (th) {
        th.addEventListener('click', function () {
          sortTable(table, th);
        });
      });
    });
  }

  function sortTable(table, th) {
    var key = th.getAttribute('data-ae-sort-key');
    var type = th.getAttribute('data-ae-sort-type') || 'number';
    var tbody = table.querySelector('tbody');
    if (!tbody) return;

    /* Determine new direction */
    var currentDir = th.getAttribute('data-ae-sort-dir');
    var newDir = currentDir === 'asc' ? 'desc' : 'asc';

    /* Clear sibling indicators */
    th.closest('thead')
      .querySelectorAll('th')
      .forEach(function (h) {
        h.removeAttribute('data-ae-sort-dir');
        h.classList.remove('ae-sort-asc', 'ae-sort-desc');
      });

    th.setAttribute('data-ae-sort-dir', newDir);
    th.classList.add(newDir === 'asc' ? 'ae-sort-asc' : 'ae-sort-desc');

    /* Sort rows */
    var rows = Array.from(tbody.querySelectorAll('tr'));
    var colIndex = Array.from(th.parentNode.children).indexOf(th);

    rows.sort(function (a, b) {
      var aVal = getCellValue(a, colIndex);
      var bVal = getCellValue(b, colIndex);

      if (type === 'number') {
        aVal = parseFloat(aVal) || 0;
        bVal = parseFloat(bVal) || 0;
        return newDir === 'asc' ? aVal - bVal : bVal - aVal;
      }

      aVal = (aVal || '').toString().toLowerCase();
      bVal = (bVal || '').toString().toLowerCase();
      if (aVal < bVal) return newDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return newDir === 'asc' ? 1 : -1;
      return 0;
    });

    /* Re-attach rows */
    rows.forEach(function (row) {
      tbody.appendChild(row);
    });
  }

  function getCellValue(row, index) {
    var cell = row.children[index];
    if (!cell) return '';
    /* Prefer data-value for numeric overrides */
    if (cell.hasAttribute('data-value')) return cell.getAttribute('data-value');
    return cell.textContent.replace(/[^0-9.\-]/g, '') || cell.textContent.trim();
  }

  /* ── 5. Stage Rail Auto-scroll ──────────────────────────────── */

  function initStageRail() {
    var current = document.querySelector('.ae-stage-rail__item.is-current');
    if (current) {
      current.scrollIntoView({ inline: 'center', block: 'nearest' });
    }
  }

  /* ── 6. Match Strip Auto-scroll ─────────────────────────────── */

  function initMatchStrip() {
    var next = document.querySelector('[data-ae-next-match]');
    if (next) {
      next.scrollIntoView({ inline: 'center', block: 'nearest' });
    }
  }

  /* ── 7. Comparison Bars — draw on intersection ──────────────── */

  function initComparisonBars() {
    var lanes = document.querySelectorAll('.ae-comparison-bars__lane > span');
    if (!lanes.length) return;

    /* Initially set width to 0, store target in data-width */
    lanes.forEach(function (bar) {
      var targetWidth = bar.style.width;
      if (targetWidth) {
        bar.setAttribute('data-target-width', targetWidth);
        bar.style.width = '0';
      }
    });

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var bar = entry.target;
            var target = bar.getAttribute('data-target-width');
            if (target) {
              bar.style.width = target;
            }
            observer.unobserve(bar);
          }
        });
      },
      { threshold: 0.1 }
    );

    lanes.forEach(function (bar) {
      observer.observe(bar);
    });
  }

  /* ── 8. Roster Wall ──────────────────────────────────────────── */

  function initRosterWall() {
    var wall = document.querySelector('.ae-roster');
    if (!wall) return;

    var cards = wall.querySelectorAll('.ae-roster__card');

    function collapseAll() {
      cards.forEach(function (c) {
        c.classList.remove('is-expanded');
        c.setAttribute('aria-expanded', 'false');
      });
      wall.classList.remove('has-expanded');
    }

    function expandCard(card) {
      var wasExpanded = card.classList.contains('is-expanded');
      collapseAll();
      if (!wasExpanded) {
        card.classList.add('is-expanded');
        card.setAttribute('aria-expanded', 'true');
        wall.classList.add('has-expanded');
      }
    }

    cards.forEach(function (card) {
      card.addEventListener('click', function (e) {
        /* Don't expand if clicking a link inside the card */
        if (e.target.closest('a')) return;
        expandCard(card);
      });

      card.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          expandCard(card);
        }
        if (e.key === 'Escape') {
          collapseAll();
        }
      });
    });

    /* Auto-expand from ?player=ID */
    var params = new URLSearchParams(window.location.search);
    var playerId = params.get('player');
    if (playerId) {
      var target = wall.querySelector('[data-player-id="' + playerId + '"]');
      if (target) {
        expandCard(target);
        setTimeout(function () {
          target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
      }
    }
  }

  /* ── 9. Breakdown Bars — draw on intersection ───────────────── */

  function initBreakdownBars() {
    var tracks = document.querySelectorAll('.ae-breakdown-bar__track > span');
    if (!tracks.length) return;

    tracks.forEach(function (bar) {
      var targetWidth = bar.style.width;
      if (targetWidth) {
        bar.setAttribute('data-target-width', targetWidth);
        bar.style.width = '0';
      }
    });

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var bar = entry.target;
            var target = bar.getAttribute('data-target-width');
            if (target) {
              bar.style.width = target;
            }
            observer.unobserve(bar);
          }
        });
      },
      { threshold: 0.1 }
    );

    tracks.forEach(function (bar) {
      observer.observe(bar);
    });
  }

  /* ── 10. Broken Image Fallback ──────────────────────────────── */

  function initImgFallback() {
    document.querySelectorAll('.ae-page img').forEach(function (img) {
      img.addEventListener('error', function () {
        this.style.visibility = 'hidden';
        this.removeAttribute('srcset');
      }, { once: true });
    });
  }

  /* ── Init ───────────────────────────────────────────────────── */

  function init() {
    initReveal();
    initAnchorNav();
    initViewToggle();
    initTableSort();
    initStageRail();
    initMatchStrip();
    initComparisonBars();
    initRosterWall();
    initBreakdownBars();
    initImgFallback();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
