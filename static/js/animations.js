document.addEventListener('DOMContentLoaded', () => {
    // Intro Animation
    const tl = gsap.timeline();

    // 1. Logo pulsing and appearing
    tl.to('.hero-logo', {
        y: 0,
        opacity: 1,
        duration: 1,
        ease: 'power3.out'
    });

    // 2. Main Title Text Reveal (Staggered)
    tl.to('.hero-title > *', {
        y: 0,
        opacity: 1,
        duration: 1.2,
        stagger: 0.15,
        ease: 'power4.out'
    }, "-=0.5");

    // 3. Label
    tl.to('.hero-label', {
        y: 0,
        opacity: 1,
        duration: 0.8,
        ease: 'power3.out'
    }, "-=1");

    // 4. Text & Counter & Button
    tl.to(['.hero-text', '.hero-counter', '.hero-btn-container'], {
        y: 0,
        opacity: 1,
        duration: 1,
        stagger: 0.2,
        ease: 'power2.out'
    }, "-=0.8");

    // 5. Player Image Slide-in (Big Reveal)
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        // На мобильных сбрасываем начальное смещение
        gsap.set('.hero-player', { x: 0 });
        // Игрок появляется с прозрачностью
        tl.to('.hero-player', {
            opacity: 0.3,
            duration: 1.2,
            ease: 'power3.out'
        }, "-=1.5");
    } else {
        // На десктопе слайд справа
        tl.to('.hero-player', {
            x: 0,
            opacity: 1,
            duration: 1.5,
            ease: 'power3.out'
        }, "-=1.5");
    }

    // 6. Scroll Indicator
    tl.from('.scroll-indicator', {
        opacity: 0,
        y: -20,
        duration: 1,
        delay: 0.5
    });

    // Scroll Animations
    if (typeof ScrollTrigger !== 'undefined') {
        gsap.registerPlugin(ScrollTrigger);

        // Cards Animation Sequence
        const wrappers = gsap.utils.toArray('.flip-card-wrapper');
        const cards = gsap.utils.toArray('.flip-card');

        if (wrappers.length > 0) {
            // Set initial state (random off-screen positions)
            const viewportW = window.innerWidth;
            const viewportH = window.innerHeight;

            wrappers.forEach((wrapper, index) => {
                const isFirst = index === 0;
                const isLast = index === wrappers.length - 1;
                const side = isFirst
                    ? 1
                    : isLast
                        ? 0
                        : Math.floor(Math.random() * 4);
                const offset = gsap.utils.random(120, 260);
                let x = 0;
                let y = 0;

                if (side === 0) {
                    // Left
                    x = -viewportW - offset;
                    y = gsap.utils.random(-viewportH * 0.2, viewportH * 1.2);
                } else if (side === 1) {
                    // Right
                    x = viewportW + offset;
                    y = gsap.utils.random(-viewportH * 0.2, viewportH * 1.2);
                } else if (side === 2) {
                    // Top
                    x = gsap.utils.random(-viewportW * 0.2, viewportW * 1.2);
                    y = -viewportH - offset;
                } else {
                    // Bottom
                    x = gsap.utils.random(-viewportW * 0.2, viewportW * 1.2);
                    y = viewportH + offset;
                }

                gsap.set(wrapper, {
                    x,
                    y,
                    opacity: 1,
                    rotation: gsap.utils.random(-25, 25),
                    scale: 0.98,
                    force3D: true
                });
            });
            
            // Set initial flip state (back visible)
            gsap.set(cards, { rotationY: 0 });

            // Create Timeline
            const cardsTl = gsap.timeline({
                scrollTrigger: {
                    trigger: '.perspective-section',
                    start: 'top 80%', // Start earlier
                    toggleActions: 'play none none none',
                    once: true
                }
            });

            // 1. Fly In (Epic Swoosh)
            cardsTl.to(wrappers, {
                x: 0,
                y: 0,
                rotation: 0,
                scale: 1,
                duration: 0.6,
                stagger: {
                    each: 0.05,
                    from: 0
                },
                ease: 'none'
            });

            // 2. Flip to front on reveal
            cardsTl.to(cards, {
                rotationY: 180,
                duration: 1.2,
                stagger: 0.08,
                ease: 'power3.inOut',
                onComplete: () => {
                    wrappers.forEach((wrapper) => {
                        const card = wrapper.querySelector('.flip-card');
                        if (card) {
                            card.flipped = true;
                        }
                    });
                }
            }, "-=0.8");

            // 3. Click-to-flip disabled
        }

        // Location & Timeline (Keep existing)
        gsap.from('.location-content', {
            scrollTrigger: {
                trigger: '.location-content',
                start: 'top 80%'
            },
            x: -50,
            opacity: 0,
            duration: 1
        });

        gsap.from('.location-map', {
            scrollTrigger: {
                trigger: '.location-content',
                start: 'top 80%'
            },
            x: 50,
            opacity: 0,
            duration: 1
        });

        gsap.utils.toArray('.timeline-item').forEach((item, i) => {
            gsap.from(item, {
                scrollTrigger: {
                    trigger: item,
                    start: 'top 85%'
                },
                y: 30,
                opacity: 0,
                duration: 0.8
            });
        });
    }
});
