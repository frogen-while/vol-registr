(function () {
  const root = document.querySelector('.match-preview-page');
  if (!root) return;

  const metricButtons = Array.from(root.querySelectorAll('.mp-metric'));
  const leaderCards = Array.from(root.querySelectorAll('.mp-leader-card'));
  const sectionLinks = Array.from(root.querySelectorAll('[data-section-link]'));
  const sections = sectionLinks
    .map((link) => document.getElementById(link.dataset.sectionLink))
    .filter(Boolean);

  function setActiveSection(sectionId) {
    sectionLinks.forEach((link) => {
      link.classList.toggle('is-active', link.dataset.sectionLink === sectionId);
    });
  }

  function updateLeaderMetric(metric) {
    metricButtons.forEach((button) => {
      button.classList.toggle('is-active', button.dataset.metric === metric);
    });

    const activeButton = root.querySelector(`.mp-metric[data-metric="${metric}"]`);
    const metricLabel = activeButton ? activeButton.textContent.trim() : metric;

    leaderCards.forEach((card) => {
      const valueNode = card.querySelector('.mp-leader-card__value');
      const labelNode = card.querySelector('.mp-leader-card__metric');
      if (!valueNode || !labelNode) return;

      valueNode.textContent = card.dataset[metric] || '-';
      labelNode.textContent = metricLabel;
    });
  }

  sectionLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      const section = document.getElementById(link.dataset.sectionLink);
      if (!section) return;

      setActiveSection(link.dataset.sectionLink);
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      window.history.replaceState(null, '', `#${link.dataset.sectionLink}`);
    });
  });

  metricButtons.forEach((button) => {
    button.addEventListener('click', () => {
      updateLeaderMetric(button.dataset.metric);
    });
  });

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        const visibleEntry = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (visibleEntry) {
          setActiveSection(visibleEntry.target.id);
        }
      },
      {
        rootMargin: '-25% 0px -55% 0px',
        threshold: [0.2, 0.4, 0.7],
      }
    );

    sections.forEach((section) => observer.observe(section));
  }

  window.addEventListener('pa_lang_change', () => {
    const activeMetric = root.querySelector('.mp-metric.is-active')?.dataset.metric || 'kills';
    updateLeaderMetric(activeMetric);
  });

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (window.gsap && !prefersReducedMotion) {
    window.gsap.from(root.querySelectorAll('.mp-reveal'), {
      y: 26,
      opacity: 0,
      duration: 0.75,
      stagger: 0.06,
      ease: 'power2.out',
      clearProps: 'all',
    });
  }

  setActiveSection(window.location.hash.replace('#', '') || 'summary');
  updateLeaderMetric('kills');
})();