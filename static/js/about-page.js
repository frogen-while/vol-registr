// About Us Page - `about-page.js`

document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Animated Counter ---
    const animatedCounters = document.querySelectorAll('[data-counter-end]');
    // ... (rest of the counter logic remains the same)
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.5,
    };

    const animateCounter = (el) => {
        const end = parseInt(el.dataset.counterEnd, 10);
        const suffix = el.dataset.counterSuffix || '';
        const duration = 2000;
        let startTime = null;

        const animation = (currentTime) => {
            if (!startTime) startTime = currentTime;
            const progress = Math.min((currentTime - startTime) / duration, 1);
            const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
            const currentCount = Math.floor(easeProgress * end);
            el.textContent = currentCount + suffix;
            if (progress < 1) requestAnimationFrame(animation);
        };
        requestAnimationFrame(animation);
    };

    const counterObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    animatedCounters.forEach(counter => counterObserver.observe(counter));
    
    // --- 2. Initialize Hero Player Slider ---
    const playerSlider = document.querySelector('.au-player-slider');
    if (playerSlider && window.Swiper) {
        new Swiper(playerSlider, {
            effect: 'coverflow',
            grabCursor: true,
            centeredSlides: true,
            loop: true,
            slidesPerView: 'auto', // This is key for coverflow
            coverflowEffect: {
                rotate: 5,
                stretch: 40,
                depth: 100,
                modifier: 1.5,
                slideShadows: false,
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            },
        });
    }

    // --- 3. Team Tabs ---
    const tabsContainer = document.querySelector('[data-tabs]');
    // ... (rest of the tabs logic remains the same)
     if (tabsContainer) {
        const tabButtons = tabsContainer.querySelectorAll('[data-tab-target]');
        const tabPanels = tabsContainer.querySelectorAll('[data-tab-panel]');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetPanelId = button.dataset.tabTarget;
                tabButtons.forEach(btn => btn.classList.remove('is-active'));
                button.classList.add('is-active');
                tabPanels.forEach(panel => {
                    panel.classList.remove('is-active');
                    if (panel.dataset.tabPanel === targetPanelId) {
                        panel.classList.add('is-active');
                    }
                });
            });
        });
    }

    // --- 4. Mouse Follow Spotlight Effect ---
    const spotlight = document.querySelector('.spotlight');
    // ... (rest of the spotlight logic remains the same)
     if(spotlight) {
        document.addEventListener('mousemove', (e) => {
            spotlight.style.background = `radial-gradient(600px circle at ${e.clientX}px ${e.clientY}px, rgba(46, 162, 248, 0.05), transparent 40%)`;
        });
    }
});
