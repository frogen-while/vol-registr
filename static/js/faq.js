// FAQ logic with delegation
document.addEventListener('DOMContentLoaded', function () {
  const faqList = document.querySelector('.faq-list');
  if (faqList) {
    faqList.addEventListener('click', function(e) {
      const btn = e.target.closest('.faq-question');
      if (!btn) return;
      
      const item = btn.closest('.faq-item');
      const isOpen = item.classList.contains('open');
      
      // Close all currently open items
      document.querySelectorAll('.faq-item.open').forEach(i => {
        // Don't close the current one yet (if we want to toggle)
        // But here we want accordion behavior (one open at a time)
        if (i !== item) {
          i.classList.remove('open');
          const b = i.querySelector('.faq-question');
          if (b) b.setAttribute('aria-expanded', 'false');
        }
      });
      
      // Toggle current
      if (isOpen) {
        item.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      } else {
        item.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  }

  // Handle Ask Question form
  const form = document.querySelector('.faq-form');
  if (form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const emailInput = form.querySelector('[name="email"]');
      const questionInput = form.querySelector('[name="question"]');
      const btn = form.querySelector('button[type="submit"]');
      
      const email = emailInput.value.trim();
      const question = questionInput.value.trim();
      
      if (!email || !question) return;
      
      // Disable button
      const originalText = btn.textContent;
      btn.disabled = true;
      btn.textContent = '...';
      
      // Get CSRF token
      let csrfToken = '';
      const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
      if (cookieMatch) csrfToken = cookieMatch[1];

      fetch('/api/ask/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ email, question })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          const successMsg = document.createElement('div');
          successMsg.className = 'faq-ask__success';
          // Use translation from navbar logic if available, or simple text
          const lang = document.documentElement.lang || 'en';
          successMsg.textContent = lang === 'pl' ? 'Pytanie wysłane!' : 'Question sent!'; 
          successMsg.style.color = '#4ade80';
          successMsg.style.marginTop = '1rem';
          successMsg.style.fontWeight = 'bold';
          
          form.querySelector('.faq-form__body').appendChild(successMsg);
          
          emailInput.value = '';
          questionInput.value = '';
          
          setTimeout(() => {
            successMsg.remove();
          }, 5000);
        } else {
          alert('Error: ' + (data.error || 'Failed to send'));
        }
      })
      .catch(err => {
        console.error(err);
        alert('Network error');
      })
      .finally(() => {
        btn.disabled = false;
        btn.textContent = originalText;
      });
    });
  }
});
