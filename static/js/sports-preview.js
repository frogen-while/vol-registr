(function () {
  const root = document.querySelector('.sp-page');
  if (!root) return;

  const sectionLinks = Array.from(root.querySelectorAll('[data-section-link]'));
  const sections = sectionLinks
    .map((link) => document.getElementById(link.dataset.sectionLink))
    .filter(Boolean);

  function setActiveSection(sectionId) {
    sectionLinks.forEach((link) => {
      link.classList.toggle('is-active', link.dataset.sectionLink === sectionId);
    });
  }

  sectionLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      const target = document.getElementById(link.dataset.sectionLink);
      if (!target) return;

      setActiveSection(link.dataset.sectionLink);
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      window.history.replaceState(null, '', `#${link.dataset.sectionLink}`);
    });
  });

  if ('IntersectionObserver' in window && sections.length) {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (visible) {
          setActiveSection(visible.target.id);
        }
      },
      {
        rootMargin: '-25% 0px -55% 0px',
        threshold: [0.2, 0.4, 0.7],
      }
    );

    sections.forEach((section) => observer.observe(section));
  }

  const toggleButtons = Array.from(root.querySelectorAll('[data-view-toggle]'));
  const toggleGroups = [...new Set(toggleButtons.map((button) => button.dataset.viewToggle))];

  function setPanelView(groupName, viewName) {
    toggleButtons.forEach((button) => {
      if (button.dataset.viewToggle === groupName) {
        const isActive = button.dataset.view === viewName;
        button.classList.toggle('is-active', isActive);
        button.setAttribute('aria-selected', String(isActive));
      }
    });

    root.querySelectorAll(`[data-view-panel="${groupName}"]`).forEach((panel) => {
      panel.classList.toggle('is-hidden', panel.dataset.view !== viewName);
    });
  }

  toggleButtons.forEach((button) => {
    button.addEventListener('click', () => {
      setPanelView(button.dataset.viewToggle, button.dataset.view);
    });
  });

  toggleGroups.forEach((groupName) => {
    const activeButton = root.querySelector(`[data-view-toggle="${groupName}"].is-active`);
    const firstButton = root.querySelector(`[data-view-toggle="${groupName}"]`);
    const nextView = activeButton?.dataset.view || firstButton?.dataset.view;
    if (nextView) {
      setPanelView(groupName, nextView);
    }
  });

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (window.gsap && !prefersReducedMotion) {
    window.gsap.from(root.querySelectorAll('.sp-reveal'), {
      y: 24,
      opacity: 0,
      duration: 0.75,
      stagger: 0.05,
      ease: 'power2.out',
      clearProps: 'all',
    });

    // Court players stagger entrance
    const courtPlayers = root.querySelectorAll('.sp-court-reveal');
    if (courtPlayers.length) {
      window.gsap.fromTo(courtPlayers,
        { y: 18, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.6, stagger: 0.12, ease: 'power2.out', delay: 0.4, clearProps: 'transform' }
      );
    }
  }

  if (window.Swiper) {
    root.querySelectorAll('[data-roster-slider]').forEach((slider) => {
      const shell = slider.closest('.sp-roster-slider-shell') || root;
      const nextEl = shell.querySelector('[data-roster-next]');
      const prevEl = shell.querySelector('[data-roster-prev]');
      const paginationEl = shell.querySelector('[data-roster-pagination]');
      const cards = Array.from(shell.querySelectorAll('[data-roster-card]'));
      const details = Array.from(shell.querySelectorAll('[data-roster-detail]'));
      const modal = shell.querySelector('[data-roster-modal]');
      const closeButtons = Array.from(shell.querySelectorAll('[data-roster-close]'));

      function getCardKey(element) {
        return element.dataset.playerId || `index-${element.dataset.playerIndex}`;
      }

      function setActiveRosterCard(nextKey) {
        cards.forEach((card) => {
          const isActive = getCardKey(card) === nextKey;
          card.classList.toggle('is-active', isActive);
          card.setAttribute('aria-expanded', String(isActive));
        });

        details.forEach((detail) => {
          detail.classList.toggle('is-active', getCardKey(detail) === nextKey);
        });
      }

      function openRosterModal(nextKey) {
        setActiveRosterCard(nextKey);
        if (modal) {
          modal.hidden = false;
          requestAnimationFrame(() => modal.classList.add('is-open'));
        }
      }

      function closeRosterModal() {
        if (!modal) return;
        modal.classList.remove('is-open');
        modal.hidden = true;
      }

      // eslint-disable-next-line no-new
      const swiper = new window.Swiper(slider, {
        slidesPerView: 1.08,
        spaceBetween: 14,
        speed: 600,
        watchOverflow: true,
        grabCursor: true,
        navigation: nextEl && prevEl ? { nextEl, prevEl } : undefined,
        pagination: paginationEl ? { el: paginationEl, clickable: true } : undefined,
        breakpoints: {
          640: { slidesPerView: 2, spaceBetween: 16 },
          980: { slidesPerView: 3, spaceBetween: 18 },
        },
      });

      cards.forEach((card) => {
        card.addEventListener('click', () => {
          const cardKey = getCardKey(card);
          openRosterModal(cardKey);
          const slideIndex = Number(card.dataset.playerIndex || 0);
          if (!Number.isNaN(slideIndex)) {
            swiper.slideTo(slideIndex);
          }
        });
      });

      closeButtons.forEach((button) => {
        button.addEventListener('click', closeRosterModal);
      });

      document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
          closeRosterModal();
        }
      });

      const queryPlayerId = new URLSearchParams(window.location.search).get('player');
      if (queryPlayerId) {
        openRosterModal(queryPlayerId);
      } else if (cards[0]) {
        setActiveRosterCard(getCardKey(cards[0]));
      }
    });
  }

  setActiveSection(window.location.hash.replace('#', '') || sectionLinks[0]?.dataset.sectionLink);

  // ── Table sorting ──────────────────────────────────────
  function initTableSort() {
    const tables = Array.from(root.querySelectorAll('table[data-sortable]'));
    tables.forEach((table) => {
      const headers = Array.from(table.querySelectorAll('th[data-sort-key]'));
      headers.forEach((th, colIndex) => {
        th.style.cursor = 'pointer';
        th.style.userSelect = 'none';
        let direction = 0; // 0 = none, 1 = asc, -1 = desc

        th.addEventListener('click', () => {
          // Reset other headers in same table
          headers.forEach((otherTh) => {
            if (otherTh !== th) {
              otherTh.dataset.sortDir = '';
              otherTh.textContent = otherTh.textContent.replace(/ [▲▼]$/, '');
            }
          });

          // Toggle direction
          direction = direction === -1 ? 1 : -1;
          th.dataset.sortDir = direction === 1 ? 'asc' : 'desc';

          // Update indicator
          const base = th.textContent.replace(/ [▲▼]$/, '');
          th.textContent = base + (direction === 1 ? ' ▲' : ' ▼');

          const tbody = table.querySelector('tbody');
          if (!tbody) return;
          const rows = Array.from(tbody.querySelectorAll('tr'));
          const isNumeric = th.dataset.sortType === 'number';

          rows.sort((a, b) => {
            const aCell = a.children[colIndex];
            const bCell = b.children[colIndex];
            if (!aCell || !bCell) return 0;
            let aVal = aCell.textContent.trim();
            let bVal = bCell.textContent.trim();

            if (isNumeric) {
              const aNum = parseFloat(aVal.replace(/[^0-9.\-]/g, '')) || 0;
              const bNum = parseFloat(bVal.replace(/[^0-9.\-]/g, '')) || 0;
              return (aNum - bNum) * direction;
            }
            return aVal.localeCompare(bVal) * direction;
          });

          rows.forEach((row) => tbody.appendChild(row));
        });
      });
    });
  }

  initTableSort();
})();