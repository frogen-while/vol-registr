/**
 * @file navbar.js
 * @description Site navigation: scroll state, mobile menu, language switcher (EN/PL)
 */

(function () {
  // ── Translations ──────────────────────────────────────────
  const T = {
    en: {
      nav_home:      'Home',
      nav_match:     'Match',
      nav_match_tip: 'Available during the tournament',
        nav_faq:       'FAQ',
        nav_register:  'Register Team',
      nav_register:  'Register Team',
    },
    pl: {
      nav_home:      'Strona Główna',
      nav_match:     'Mecze',
      nav_match_tip: 'Dostępne podczas turnieju',
        nav_faq:       'FAQ',
        nav_register:  'Zarejestruj Drużynę',
      nav_register:  'Zarejestruj Drużynę',
    },
  };

  // ── State ─────────────────────────────────────────────────
  let lang = localStorage.getItem('pa_lang') || 'en';

  // ── DOM refs ──────────────────────────────────────────────
  const nav      = document.getElementById('siteNav');
  const menu     = document.getElementById('navMenu');
  const burger   = document.getElementById('navBurger');
  const overlay  = document.getElementById('navOverlay');
  const langWrap = document.getElementById('langToggle');

  // ── Apply language ────────────────────────────────────────
  function applyLang(l) {
    lang = l;
    localStorage.setItem('pa_lang', l);
    const t = T[l] || T.en;

    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      if (t[key] !== undefined) el.textContent = t[key];
    });

    // update button active states
    document.querySelectorAll('.site-nav__lang-opt').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === l);
    });

    document.documentElement.lang = l;
  }

  // ── Scroll state ──────────────────────────────────────────
  function onScroll() {
    if (!nav) return;
    nav.classList.toggle('scrolled', window.scrollY > 30);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll(); // init

  // ── Mobile burger ─────────────────────────────────────────

  function setMenuOpen(open) {
    menu.classList.toggle('open', open);
    burger.classList.toggle('open', open);
    burger.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('nav-open', open);
    document.documentElement.classList.toggle('nav-open', open);
    overlay && overlay.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
    document.documentElement.style.overflow = open ? 'hidden' : '';
  }

  burger && burger.addEventListener('click', () => {
    setMenuOpen(!menu.classList.contains('open'));
  });

  // Overlay click closes menu
  overlay && overlay.addEventListener('click', () => {
    setMenuOpen(false);
  });

  // Close menu when nav link is clicked
  menu && menu.addEventListener('click', e => {
    if (e.target.closest('.site-nav__link, .site-nav__cta')) {
      setMenuOpen(false);
    }
  });

  // ── Language switcher ─────────────────────────────────────
  langWrap && langWrap.addEventListener('click', e => {
    const btn = e.target.closest('[data-lang]');
    if (btn) applyLang(btn.dataset.lang);
  });

  // ── Init ──────────────────────────────────────────────────
  applyLang(lang);
})();
