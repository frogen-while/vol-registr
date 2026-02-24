document.addEventListener("DOMContentLoaded", () => {
            
    // 1. Анімація появи елементів (Intro)
    const tl = gsap.timeline();

    // Текст зліва
    tl.from(".gsap-hero-text > *", {
        y: 40,
        opacity: 0,
        duration: 1,
        stagger: 0.15,
        ease: "power3.out"
    })
    // Панель форми справа
    .from(".gsap-form-panel", {
        x: 50,
        opacity: 0,
        duration: 1,
        ease: "power3.out"
    }, "-=0.8")
    // Поля форми каскадом
    .from(".gsap-form-field", {
        y: 20,
        opacity: 0,
        duration: 0.8,
        stagger: 0.1,
        ease: "power2.out"
    }, "-=0.6")
    // Поява 3D картки
    .from(".gsap-pass", {
        scale: 0.5,
        opacity: 0,
        rotateX: -30,
        duration: 1.5,
        ease: "back.out(1.5)"
    }, "-=1");

    // 2. Безперервна 3D левітація картки (Idle Animation)
    // Обгортка рухається вгору-вниз
    gsap.to(".pass-container", {
        y: -15,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
    });

    // Сама картка повільно обертається навколо своєї осі
    gsap.to("#vipPass", {
        rotateY: 360,
        duration: 15,
        repeat: -1,
        ease: "none"
    });

    // Додаємо невеликий нахил картки в залежності від руху миші
    const passElement = document.getElementById('vipPass');
    const passContainer = document.querySelector('.pass-container');
    
    if (passContainer && passElement) {
        passContainer.addEventListener('mousemove', (e) => {
            const rect = passContainer.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            
            // Зупиняємо базове обертання під час ховеру
            gsap.killTweensOf(passElement, "rotateY");
            
            gsap.to(passElement, {
                rotateY: x * 0.1,
                rotateX: -y * 0.1,
                duration: 0.5,
                ease: "power1.out"
            });
        });

        passContainer.addEventListener('mouseleave', () => {
            // Відновлюємо базове обертання
            gsap.to(passElement, {
                rotateX: 0,
                rotateY: "+=360",
                duration: 15,
                repeat: -1,
                ease: "none",
                delay: 0.5 // невелика затримка перед поверненням
            });
        });
    }

    // 3. Обробка відправки форми
    const form = document.getElementById('registrationForm');
    const submitBtn = document.getElementById('submitBtn');
    const successMessage = document.getElementById('successMessage');
    
    // Helper to get CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Анімація кнопки "Завантаження"
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="relative z-10">Processing...</span>';
            submitBtn.style.opacity = '0.8';
            submitBtn.disabled = true;

            // Збір даних
            const data = {
                teamName: document.getElementById('teamName').value,
                division: document.getElementById('division').value,
                city: document.getElementById('city').value,
                capName: document.getElementById('capName').value,
                phone: document.getElementById('phone').value,
                email: document.getElementById('email').value,
                roster: document.getElementById('roster').value
            };

            const csrftoken = getCookie('csrftoken');

            // Реальний запит на сервер
            fetch('/api/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Успіх - запускаємо анімацію
                    gsap.to(".gsap-form-field", {
                        y: -20,
                        opacity: 0,
                        duration: 0.4,
                        stagger: 0.05,
                        ease: "power2.in",
                        onComplete: () => {
                            // Приховуємо поля
                            const fields = document.querySelectorAll('.gsap-form-field');
                            fields.forEach(f => f.classList.add('hidden'));
                            
                            successMessage.classList.remove('hidden');
                            
                            // Анімація появи повідомлення
                            gsap.from(successMessage, {
                                scale: 0.9,
                                opacity: 0,
                                duration: 0.6,
                                ease: "back.out(1.5)"
                            });

                            // Оновлюємо ID на картці (якщо сервер повертає ID)
                            // Можна додати логіку тут

                            // Святкування карткою
                            gsap.to("#vipPass", {
                                rotateY: "+=720",
                                duration: 2,
                                ease: "power2.inOut",
                                onComplete: () => {
                                    gsap.to("#vipPass", { rotateY: "+=360", duration: 15, repeat: -1, ease: "none" });
                                }
                            });
                        }
                    });
                } else {
                    // Помилка
                    alert('Registration Error: ' + result.error);
                    submitBtn.innerHTML = originalText;
                    submitBtn.style.opacity = '1';
                    submitBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
                submitBtn.innerHTML = originalText;
                submitBtn.style.opacity = '1';
                submitBtn.disabled = false;
            });
        });
    }
});

// Tailwind custom animation config (needs to remain in HTML script block or via tailwind.config.js usually, but we keep basic logic here if needed)
