/**
 * @file navbar.js
 * @description Site navigation: scroll state, mobile menu, language switcher (EN/PL)
 */

(function () {
  // ── Translations ──────────────────────────────────────────
  const T = {
    en: {
      // Main page (index.html)
      hero: {
        label: 'April 11, 2026 • Rzgów, Szkolna 5',
        title: { main: 'POCKET ACES', sub: 'SPRING TOURNAMENT 2026' },
        text: 'The first official tournament by Pocket Aces Sports Club, organized by a team of over 20 members. Built around professional organization, a competitive format, and high standards.',
        price: { label: 'per team' },
        counter: { label: 'Teams Registered' },
        cta: 'Secure Your Spot'
      },
      deal: {
        heading: 'The Deal',
        card1: {
          title: 'Grand Prize',
          text: 'Top 3 teams receive official Pocket Aces trophies and medals, with individual MVP awards presented to the best players of the tournament.',
          list1: 'Championship Trophy',
          list2: 'Medals for Top 3 Teams',
          list3: '6 MVP Awards'
        },
        card2: {
          title: 'Competitive Format',
          text: 'Group stage followed by single-elimination playoffs. All matches are played to two winning sets with rally scoring.',
          list1: 'Group Stage + Playoffs',
          list2: 'Minimum 2 Games Guaranteed'
        },
        card3: {
          title: 'High Level Organization',
          text: 'A team of up to 20 organizers ensures smooth operation across every aspect of the event — from logistics and scheduling to live scoring and on-court officiating.',
          list1: 'Fixed Match Schedule',
          list2: 'Live Score Tracking'
        },
        card4: {
          title: 'Full Day Experience',
          text: 'A full day of competitive volleyball, team camaraderie, and real tournament atmosphere.',
          list1: 'Professional Venue & Equipment',
          list2: 'Post-Tournament Highlights'
        }
      },
      location: {
        title: 'The Arena',
        text: 'Join us in Rzgów, Poland for an unforgettable experience. The venue features professional-grade courts, changing rooms, and a spectator area.',
        info: { label: 'Location', value: 'Rzgów, Szkolna 5' },
        date: { label: 'Date', value: 'April 11, 2026' },
        link: 'View on Google Maps'
      },
      registered: {
        cta: 'See registered teams ->',
        modal_title: 'Registered Teams',
        modal_subtitle: 'Pocket Aces Spring Tournament',
        col_team: 'Team',
        col_captain: 'Captain',
        col_level: 'Level',
        empty: 'No registered teams.'
      },
      arena: { heading: 'The Venue' },
      // Road to Victory
      road: {
        heading: 'Road to Victory',
        step1: { date: 'March 1', title: 'Registration Opens', desc: 'Team registration begins. Secure your spot early as places are limited.' },
        step2: { date: 'April 5', title: 'Registration Closes', desc: 'Last day to register your team and submit the roster.' },
        step3: { date: 'April 8', title: 'Schedule Release', desc: 'Match schedule and groups will be published and sent to captains.' },
        step4: { date: 'April 11', title: 'Tournament Day', desc: 'The big day! Group stage matches start at 9:00 AM.' }
      },
      // FAQ page
      faq: {
        title: 'FAQ',
        q1: 'What if a player is under 18?',
        a1: 'If any player is under 18, a <a href="/static/assets/documents/ZGODA_RODZICA_Pocket_Aces_12_04_2026.pdf" target="_blank">parental consent form</a> must be filled out and provided at registration.',
        q2: "What if our team doesn't have uniforms?",
        a2: 'You must make your numbers clearly visible by any means. If not, your team will not receive detailed statistics.',
        q3: 'Can we get a refund?',
        a3: 'Yes, you can get a refund until the end of registration. Just contact support.',
        q4: 'Can we bring spectators?',
        a4: 'Absolutely! There are seats for spectators in the hall.',
        q5: 'How many players can be on a team?',
        a5: 'A team can have 6 to 12 players, including substitutes.',
        q6: 'Can we change a player after registration?',
        a6: 'Yes, you can replace a player before the tournament starts by notifying the organizers.',
        q7: 'Where can we find the match schedule?',
        a7: 'The match schedule will be published on the website and sent to team captains by email a few days before the tournament.',
        ask_title: 'Ask a question',
        ask_email_ph: 'Your email',
        ask_question_ph: 'Your question',
        ask_btn: 'Send',
        ask_success: 'Question sent!'
      },
      nav_home:      'Home',
      nav_match:     'Match',
      nav_match_tip: 'Available during the tournament',
      nav_faq:       'FAQ',
      nav_register:  'Register Team',
      footer_nav: 'Navigation',
      footer_documents: 'Documents',
      footer_connect: 'Connect',
      footer_about: 'About',
      footer_identity: 'Pocket Aces Sport Club — community-run volleyball club organizing local tournaments and events.',
      site_identity: 'Pocket Aces Sport Club — community-run volleyball club organizing local tournaments and events.',
      reg_step1:     'Team',
      reg_step2:     'Captain',
      reg_step3:     'Roster',
      reg_title:     'Official Registration',
      reg_subtitle:  'Pocket\nAces\nInvitational',
      reg_desc:      "We’re starting to put together the lineup for our 2026 volleyball tournament. We have space for 12 teams this time around, so if you're planning to join us, make sure to sign up early to grab a spot. ",
      reg_identity:  'Team Identity',
      reg_team_name: 'Team Name',
      reg_team_ph:   'e.g. Warsaw Eagles',
      reg_league:    'League Level',
      reg_1st:       '1st Liga',
      reg_2nd:       '2nd Liga',
      reg_3rd:       '3rd Liga',
      reg_indep:     'Independent Team',
      reg_ig:        'Instagram Handle',
      reg_ig_ph:     'yourteam',
      reg_next1:     'Next: Captain',
      reg_captain:   'Captain Details',
      reg_fullname:  'Full Name',
      reg_fullname_ph: 'e.g. Jan Kowalski',
      reg_phone:     'Phone Number',
      reg_phone_ph:  '+48 123 456 789',
      reg_email:     'Email Address',
      reg_email_ph:  'captain@yourteam.com',
      reg_next2:     'Next: Roster',
      reg_back:      'Back',
      reg_roster:    'Team Roster',
      reg_hint:      'Minimum 6 players required',
      reg_note:      '<strong>Important:</strong><br>Captain must be listed as one of the players below.<br><br>If any player is under 18, a <a href="/static/assets/documents/ZGODA_RODZICA_Pocket_Aces_12_04_2026.pdf" target="_blank">parental consent form</a> must be filled out and provided at registration.<br><br>Jersey numbers are optional, but if <strong>any</strong> player is missing a number, the <strong>entire team will not receive match statistics</strong>.',
      reg_first:     'First Name',
      reg_last:      'Last Name',
      reg_jersey:    '#',
      reg_add:       '+ Add Player',
      reg_terms:     'I have read and accept the <a href="/static/assets/documents/Regulations_english.pdf" target="_blank">tournament regulations</a>',
      reg_age:       'All players are 18 years of age or older',
        reg_parental:  'If any player is under 18, a <a href="/static/assets/documents/ZGODA_RODZICA_Pocket_Aces_12_04_2026.pdf" target="_blank">parental consent form</a> must be filled out and provided at registration.',
      reg_photo:     'I consent to photos/videos being taken during the event',
      reg_payment:   'I understand the entry fee is <strong>400 PLN</strong> and payment details will be sent by email',
      reg_submit:    'Register Team',
      reg_success:   'Registration Submitted!',
      reg_success_txt: 'Your team has been registered. Payment instructions will be sent to your email address shortly.',
      // Validation
      err_team_name: 'Team name is required.',
      err_league:    'Please select a league level.',
      err_fullname:  'Please enter first and last name.',
      err_phone:     'Phone number is required.',
      err_email:     'Please enter a valid email address.',
      err_players:   'At least 6 players are required (currently {n}).',
      err_checks:    'Please accept all required checkboxes to continue.',
      err_network:   'Network error. Please check your connection and try again.',
      err_failed:    'Registration failed. Please try again.',
      
      // Team detail page
      team_back: 'Back to teams list',
      team_captain: 'Captain',
      team_roster: 'Team Roster',
      team_name: 'First and Last Name',
      team_jersey: 'Jersey Number',
      team_email: 'Email',
      team_phone: 'Phone',
      team_mail_to: 'Mail to',
      team_call: 'Call',
      team_empty: 'No players added.'
    },
    pl: {
      // Main page (index.html)
      hero: {
        label: '11 kwietnia 2026 • Rzgów, Szkolna 5',
        title: { main: 'POCKET ACES', sub: 'WIOSENNY TURNIEJ 2026' },
        text: 'Pierwszy oficjalny turniej klubu Pocket Aces Sports, organizowany przez zespół ponad 20 członków. Profesjonalna organizacja, konkurencyjny format i wysokie standardy.',
        price: { label: 'za drużynę' },
        counter: { label: 'Zarejestrowane drużyny' },
        cta: 'Zarezerwuj miejsce'
      },
      deal: {
        heading: 'Stawka',
        card1: {
          title: 'Nagroda Główna',
          text: '3 najlepsze drużyny otrzymają oficjalne trofea Pocket Aces i medale, a indywidualne nagrody MVP zostaną wręczone najlepszym zawodnikom turnieju.',
          list1: 'Trofeum Mistrzowskie',
          list2: 'Medale dla 3 najlepszych drużyn',
          list3: '6 nagród MVP'
        },
        card2: {
          title: 'Konkurencyjny Format',
          text: 'Faza grupowa, a następnie play-offy. Wszystkie mecze do dwóch wygranych setów, punktacja rally.',
          list1: 'Faza grupowa + play-offy',
          list2: 'Gwarantowane minimum 2 mecze'
        },
        card3: {
          title: 'Organizacja na Wysokim Poziomie',
          text: 'Zespół do 20 organizatorów zapewnia sprawne działanie każdego aspektu wydarzenia — od logistyki i harmonogramu po live scoring i sędziowanie.',
          list1: 'Stały harmonogram meczów',
          list2: 'Live scoring'
        },
        card4: {
          title: 'Całodniowe Wydarzenie',
          text: 'Cały dzień rywalizacji, drużynowej atmosfery i prawdziwego turniejowego klimatu.',
          list1: 'Profesjonalny obiekt i sprzęt',
          list2: 'Relacja po turnieju'
        }
      },
      location: {
        title: 'Arena',
        text: 'Dołącz do nas w Rzgowie, Polska, na niezapomniane wydarzenie. Obiekt posiada profesjonalne boiska, szatnie i trybuny dla widzów.',
        info: { label: 'Lokalizacja', value: 'Rzgów, Szkolna 5' },
        date: { label: 'Data', value: '11 kwietnia 2026' },
        link: 'Zobacz na Google Maps'
      },
      registered: {
        cta: 'Zobacz zarejestrowane drużyny ->',
        modal_title: 'Zarejestrowane Drużyny',
        modal_subtitle: 'Pocket Aces Spring Tournament',
        col_team: 'Drużyna',
        col_captain: 'Kapitan',
        col_level: 'Poziom',
        empty: 'Brak zarejestrowanych drużyn.'
      },
      arena: { heading: 'Obiekt' },
      // Road to Victory
      road: {
        heading: 'Droga do Zwycięstwa',
        step1: { date: '1 marca', title: 'Otwarcie Rejestracji', desc: 'Rozpoczęcie rejestracji drużyn. Zarezerwuj miejsce wcześniej, liczba miejsc ograniczona.' },
        step2: { date: '5 kwietnia', title: 'Koniec Rejestracji', desc: 'Ostatni dzień na rejestrację drużyny i przesłanie składu.' },
        step3: { date: '8 kwietnia', title: 'Publikacja Harmonogramu', desc: 'Harmonogram meczów i grupy zostaną opublikowane i wysłane do kapitanów.' },
        step4: { date: '11 kwietnia', title: 'Dzień Turnieju', desc: 'Wielki dzień! Mecze fazy grupowej rozpoczynają się o 9:00.' }
      },
      // FAQ page
      faq: {
        title: 'FAQ',
        q1: 'Co jeśli zawodnik ma mniej niż 18 lat?',
        a1: 'Jeśli którykolwiek z zawodników ma mniej niż 18 lat, należy wypełnić <a href="/static/assets/documents/ZGODA_RODZICA_Pocket_Aces_12_04_2026.pdf" target="_blank">zgodę rodzica</a> i dostarczyć ją organizatorom.',
        q2: 'Co jeśli drużyna nie ma strojów?',
        a2: 'Numery muszą być wyraźnie widoczne w dowolny sposób. W przeciwnym razie drużyna nie otrzyma szczegółowych statystyk.',
        q3: 'Czy można otrzymać zwrot opłaty?',
        a3: 'Tak, zwrot jest możliwy do końca rejestracji. Skontaktuj się z organizatorami.',
        q4: 'Czy można przyprowadzić kibiców?',
        a4: 'Oczywiście! Na hali są miejsca dla kibiców.',
        q5: 'Ilu zawodników może być w drużynie?',
        a5: 'Drużyna może liczyć od 6 do 12 zawodników, w tym rezerwowych.',
        q6: 'Czy można zmienić zawodnika po rejestracji?',
        a6: 'Tak, można wymienić zawodnika przed turniejem, informując organizatorów.',
        q7: 'Gdzie znajdziemy harmonogram meczów?',
        a7: 'Harmonogram zostanie opublikowany na stronie i wysłany kapitanom drużyn e-mailem kilka dni przed turniejem.',
        ask_title: 'Zadaj pytanie',
        ask_email_ph: 'Twój email',
        ask_question_ph: 'Twoje pytanie',
        ask_btn: 'Wyślij',
        ask_success: 'Pytanie wysłane!'
      },
      nav_home:      'Strona Główna',
      nav_match:     'Mecze',
      nav_match_tip: 'Dostępne podczas turnieju',
      nav_faq:       'FAQ',
      nav_register:  'Zarejestruj Drużynę',
      footer_nav: 'Nawigacja',
      footer_documents: 'Dokumenty',
      footer_connect: 'Kontakt',
      footer_about: 'O nas',
      footer_identity: 'Pocket Aces Sport Club — lokalny klub siatkówki organizujący turnieje i wydarzenia.',
      site_identity: 'Pocket Aces Sport Club — lokalny klub siatkówki organizujący turnieje i wydarzenia.',
      reg_step1:     'Drużyna',
      reg_step2:     'Kapitan',
      reg_step3:     'Skład',
      reg_title:     'Oficjalna Rejestracja',
      reg_subtitle:  'Pocket\nAces\nInvitational',
      reg_desc:      'Zaczynamy kompletować listę drużyn na nasz turniej siatkówki 2026. Tym razem mamy miejsce dla 12 zespołów, więc jeśli planujecie do nas dołączyć, warto zarejestrować się wcześniej, żeby zaklepać sobie miejsce.',
      reg_identity:  'Tożsamość Drużyny',
      reg_team_name: 'Nazwa Drużyny',
      reg_team_ph:   'np. Warsaw Eagles',
      reg_league:    'Poziom Ligi',
      reg_1st:       '1 Liga',
      reg_2nd:       '2 Liga',
      reg_3rd:       '3 Liga',
      reg_indep:     'Drużyna Niezależna',
      reg_ig:        'Instagram',
      reg_ig_ph:     'twojadruzyna',
      reg_next1:     'Dalej: Kapitan',
      reg_captain:   'Dane Kapitana',
      reg_fullname:  'Imię i Nazwisko',
      reg_fullname_ph: 'np. Jan Kowalski',
      reg_phone:     'Telefon',
      reg_phone_ph:  '+48 123 456 789',
      reg_email:     'E-mail',
      reg_email_ph:  'kapitan@twojadruzyna.com',
      reg_next2:     'Dalej: Skład',
      reg_back:      'Wstecz',
      reg_roster:    'Skład Drużyny',
      reg_hint:      'Minimum 6 zawodników',
      reg_note:      '<strong>Ważne:</strong><br>Kapitan musi być wymieniony jako jeden z zawodników poniżej.<br><br>Jeśli którykolwiek z zawodników ma mniej niż 18 lat, należy wypełnić <a href="/static/assets/documents/ZGODA_RODZICA_Pocket_Aces_12_04_2026.pdf" target="_blank">zgodę rodzica</a> i dostarczyć ją organizatorom.<br><br>Numery na koszulkach są opcjonalne, ale jeśli <strong>ktokolwiek</strong> nie będzie miał numeru, <strong>cała drużyna nie otrzyma statystyk meczowych</strong>.',
      reg_first:     'Imię',
      reg_last:      'Nazwisko',
      reg_jersey:    '#',
      reg_add:       '+ Dodaj Zawodnika',
      reg_terms:     'Przeczytałem i akceptuję <a href="/static/assets/documents/Regulations_polish.pdf" target="_blank">regulamin turnieju</a>',
      reg_age:       'Wszyscy zawodnicy mają ukończone 18 lat',
        reg_parental:  'Jeśli którykolwiek z zawodników ma mniej niż 18 lat, należy wypełnić <a href="/static/assets/documents/ZGODA_RODZICA_Pocket_Aces_12_04_2026.pdf" target="_blank">zgodę rodzica</a> i dostarczyć ją organizatorom.',
      reg_photo:     'Wyrażam zgodę na zdjęcia/filmy podczas wydarzenia',
      reg_payment:   'Rozumiem, że wpisowe wynosi <strong>400 PLN</strong>, a szczegóły płatności zostaną przesłane e-mailem',
      reg_submit:    'Zarejestruj Drużynę',
      reg_success:   'Rejestracja Zakończona!',
      reg_success_txt: 'Twoja drużyna została zarejestrowana. Instrukcje dotyczące płatności zostaną przesłane na Twój adres e-mail.',
      // Validation
      err_team_name: 'Nazwa drużyny jest wymagana.',
      err_league:    'Wybierz poziom ligi.',
      err_fullname:  'Podaj imię i nazwisko.',
      err_phone:     'Telefon jest wymagany.',
      err_email:     'Podaj prawidłowy e-mail.',
      err_players:   'Wymaganych jest co najmniej 6 graczy (obecnie {n}).',
      err_checks:    'Zaakceptuj wszystkie wymagane pola wyboru.',
      err_network:   'Błąd sieci. Sprawdź połączenie.',
      err_failed:    'Rejestracja nie powiodła się. Spróbuj ponownie.',
      
      // Team detail page
      team_back: 'Wróć do listy drużyn',
      team_captain: 'Kapitan',
      team_roster: 'Skład Drużyny',
      team_name: 'Imię i Nazwisko',
      team_jersey: 'Numer Koszulki',
      team_email: 'Email',
      team_phone: 'Telefon',
      team_mail_to: 'Napisz',
      team_call: 'Zadzwoń',
      team_empty: 'Brak dodanych graczy.'
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
      const value = key.split('.').reduce((acc, k) => (acc && acc[k] !== undefined ? acc[k] : undefined), t);
      if (value !== undefined) {
        // Для FAQ-ответов и специальных заметок используем innerHTML
        if (/^faq\.a\d+$/.test(key) || key === 'reg_note' || key === 'reg_parental' || key === 'reg_payment' || key === 'reg_terms') {
          el.innerHTML = value;
        } else {
          el.textContent = value;
        }
      }
    });

    // Update placeholders
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      const key = el.dataset.i18nPh;
      const value = key.split('.').reduce((acc, k) => (acc && acc[k] !== undefined ? acc[k] : undefined), t);
      if (value !== undefined) el.placeholder = value;
    });

    // update button active states
    document.querySelectorAll('.site-nav__lang-opt').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === l);
    });

    document.documentElement.lang = l;

    // Broadcast language change for other scripts
    window.dispatchEvent(new CustomEvent('pa_lang_change', { detail: l }));
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
    // document.body.style.overflow = open ? 'hidden' : '';
    // document.documentElement.style.overflow = open ? 'hidden' : '';
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
