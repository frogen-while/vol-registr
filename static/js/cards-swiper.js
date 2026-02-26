/**
 * Cards Swiper — mobile-only carousel
 * Stacked cards effect with swipe
 */
(function () {
  'use strict';

  const MOBILE_BP = 768;
  let swiperInstance = null;

  function initSwiper() {
    if (swiperInstance) return;
    swiperInstance = new Swiper('.cards-swiper', {
      effect: 'cards',
      grabCursor: true,
      speed: 500,
      cardsEffect: {
        perSlideOffset: 8,
        perSlideRotate: 3,
        rotate: true,
        slideShadows: false,
      },
      pagination: {
        el: '.cards-pagination',
        clickable: true,
      },
    });
  }

  function destroySwiper() {
    if (!swiperInstance) return;
    swiperInstance.destroy(true, true);
    swiperInstance = null;

    // Clean up residual inline styles left by Swiper
    var wrapper = document.querySelector('.cards-swiper .swiper-wrapper');
    if (wrapper) wrapper.removeAttribute('style');
    var slides = document.querySelectorAll('.cards-swiper .swiper-slide');
    slides.forEach(function (s) { s.removeAttribute('style'); });
  }

  function handleResize() {
    if (window.innerWidth < MOBILE_BP) {
      initSwiper();
    } else {
      destroySwiper();
    }
  }

  // Init on load
  document.addEventListener('DOMContentLoaded', handleResize);

  // Re-check on resize (debounced)
  let resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(handleResize, 150);
  });
})();
