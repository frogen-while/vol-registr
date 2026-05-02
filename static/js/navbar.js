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
        label: 'June 6 • 09:00 • Outdoor Court by Dormitory No. 8',
        title: {
          intro_top: 'POCKET',
          intro_bottom: 'ACES',
          final_top: 'LUMUMBY',
          final_bottom: 'CUP 2'
        },
        text: 'Registration is open for Pocket Aces Lumumby Cup 2. Outdoor play, 8 teams, first serve at 09:00. Lock your spot before registration closes on June 3.',
        mobile_fact1: 'Tournament Day',
        mobile_fact2: 'Team Limit',
        mobile_fact3: 'Outdoor Court',
        price: { label: 'per team' },
        counter: { label: 'Teams Registered' },
        cta: 'Join Tournament',
        closed: 'Registration Closed'
      },
      voting: {
        title: 'Fan Favorite',
        subtitle: 'Most Popular Team',
        count: 'Fans',
        cta: 'Vote'
      },
      deal: {
        heading: 'Why Register',
        card1: {
          title: 'Prizes',
          text: 'The podium plays for cups and medals. No side awards, no filler, just a clean race for the top spots.',
          list1: 'Cups for the winners',
          list2: 'Medals for top teams',
          list3: 'One-day trophy chase'
        },
        card2: {
          title: 'Registration',
          text: 'Registration is live now and only 8 teams make the field. Secure your place before the June 3 deadline.',
          list1: 'Deadline: June 3',
          list2: 'Entry fee: 150 zł'
        },
        card3: {
          title: 'Outdoor Matchday',
          text: 'We meet at the outdoor court by Dormitory No. 8 on June 6 at 09:00 for a full tournament day.',
          list1: 'Court by Dormitory No. 8',
          list2: 'Arrive 30-60 min early'
        },
        card4: {
          title: 'Weather Policy',
          text: 'This is an outdoor event. If the weather turns bad, the tournament may be postponed and captains will be informed directly.',
          list1: 'Outdoor format',
          list2: 'Updates sent to captains'
        }
      },
      deal_lead: 'A compact outdoor event built for teams that want a sharp schedule, clear stakes, and a better matchday atmosphere.',
      location: {
        kicker: 'Venue Details',
        title: 'The Venue',
        text: 'Pocket Aces Lumumby Cup 2 moves to the outdoor court next to Dormitory No. 8 in Łódź. Bring your team 30-60 minutes early for registration and warm-up.',
        info: { label: 'Location', value: 'Strajku Łódzkich Studentów 1981 r. 2, 91-404 Łódź' },
        date: { label: 'Date', value: 'June 6, 09:00' },
        link: 'View on Google Maps'
      },
      location_pill1_title: 'Open-Air Setup',
      location_pill1_copy: 'Fresh air, one focused court, and a tournament rhythm that stays tight from morning to final whistle.',
      location_pill2_title: 'Easy Logistics',
      location_pill2_copy: 'Quick arrival, simple captain communication, and a venue layout that keeps the day moving.',
      location_pill3_title: 'Compact Match Flow',
      location_pill3_copy: 'Short resets, clear sideline spacing, and enough room to keep every round feeling sharp.',
      registered: {
        cta: 'See teams ->',
        modal_title: 'Registered Teams',
        modal_subtitle: 'Pocket Aces Lumumby Cup 2',
        col_team: 'Team',
        col_captain: 'Captain',
        col_level: 'Level',
        empty: 'No registered teams.'
      },
      arena: { heading: 'The Venue' },
      arena_note: 'A cleaner outdoor setting, compact surroundings, and enough atmosphere to make the whole day feel like a proper event.',
      // Road to Victory
      road: {
        heading: 'Registration Timeline',
        lead: 'From sign-up to first serve, these are the four moments that shape the event week.',
        step1: { date: 'Open now', title: 'Now Open', desc: 'Team registration is open. Join now before all 8 spots are taken.' },
        step2: { date: 'June 3', title: 'Registration Closes', desc: 'Final deadline to lock your team into the event.' },
        step3: { date: 'After close', title: 'Captain Update', desc: 'Final event details will be sent to registered captains.' },
        step4: { date: 'June 6, 09:00', title: 'Tournament Day', desc: 'Pocket Aces Lumumby Cup 2 starts at the outdoor court by Dormitory No. 8.' }
      },
      gallery_page: {
        eyebrow: 'Pocket Aces',
        title: 'Gallery',
        subtitle: 'Photos and video highlights from Pocket Aces Lumumby Cup 2.',
        photos_title: 'Photos',
        videos_title: 'Video Highlights',
        prev_title: 'Previous Tournament',
        prev_subtitle: 'Media Archive',
        empty: 'Gallery will be updated once Pocket Aces Lumumby Cup 2 starts.'
      },
      // FAQ page
      faq: {
        title: 'FAQ',
        q1: 'What if a player is under 18?',
        a1: 'If any player is under 18, a <a href="/static/assets/documents/ZGODA_RODZICA_Pocket_Aces_12_04_2026_1.pdf" target="_blank">parental consent form</a> must be sent before the event and brought in paper form on tournament day.',
        q2: "What if our team doesn't have uniforms?",
        a2: 'Uniform numbers are not required. Matching shirts are welcome, but the key point is that your team stays easy to identify on court.',
        q3: 'Can we get a refund?',
        a3: 'If the tournament is canceled because the minimum number of teams is not reached, all payments are refunded within 7 days.',
        q4: 'What happens if the weather is bad?',
        a4: 'Because this is an open-air event, the tournament may be postponed in case of bad weather. Registered captains will be informed directly.',
        q5: 'How many players can be on a team?',
        a5: 'You need 6 players on court to start a match, and you can register an unlimited number of substitutes.',
        q6: 'Can we change a player after registration?',
        a6: 'Roster changes are accepted only until registration closes on June 3. Once the tournament starts, roster changes are not allowed.',
        q7: 'Where can we find the match schedule?',
        a7: 'The final format depends on the number of registered teams. Captains receive updates directly, and key schedule information will also appear on the website.',
        ask_title: 'Ask a question',
        ask_email_ph: 'Your email',
        ask_question_ph: 'Your question',
        ask_btn: 'Send',
        ask_success: 'Question sent!'
      },
      cs: {
        heading: 'Match Centre Soon',
        sub: 'Match Centre opens on <strong>June 6 at 09:00</strong>. Until then, use the time left to register your team for Pocket Aces Lumumby Cup 2.',
        days: 'Days',
        hours: 'Hours',
        min: 'Min',
        sec: 'Sec',
        live: 'Match day is here.',
        reloading: 'See you on court.',
        groups_heading: 'Groups',
        roster_btn: 'Join Tournament',
        back: 'Back to Home',
      },
      rp: {
        title: 'Team Profile Access',
        heading: 'Manage Your <span>Team</span>',
        subtitle: 'Captains can update the roster, refresh the badge, and keep contact details current in one place.',
        logo_title: 'Team Badge',
        logo_copy: 'Upload or replace the square badge. PNG, JPG, or WebP up to 5 MB works best.',
        logo_drop: 'Drop a square badge here or browse',
        logo_hint: 'Optional, but recommended for the public team list.',
        logo_empty: 'No badge yet',
        choose_file: 'Choose File',
        no_file: 'No file chosen',
        upload_logo: 'Upload Logo',
        profile_title: 'Team Details',
        profile_copy: 'These details are used for payment follow-up, final reminders, and public team presentation.',
        profile_subtitle: 'Keep your team page current before match day. Update names, contacts, and the square badge anytime.',
        team_name: 'Team Name',
        captain_name: 'Captain Name',
        captain_email: 'Captain Email',
        captain_phone: 'Captain Phone',
        roster_title: 'Roster',
        roster_subtitle: 'Keep at least 6 players. Add or remove players whenever the squad changes.',
        roster_rule: 'Keep at least 6 players on the roster.',
        player_first: 'First Name',
        player_first_ph: 'First Name',
        player_last: 'Last Name',
        player_last_ph: 'Last Name',
        player_remove: 'Remove',
        players_chip: 'players',
        add_player: 'Add Player',
        save_profile: 'Save Changes',
        start_over: 'Use Another Team',
        save: 'Save Roster',
        cancel: 'Cancel',
        enter_code: 'Use Backup Code',
        code_hint: 'We also sent a backup code by email. If the magic link is unavailable, enter the code here.',
        access_code_label: 'Access code',
        code_ph: 'Enter backup code',
        verify: 'Verify Code',
        back: 'Back',
        select_team: 'Choose Your Team',
        select_hint: 'Pick your team and we will send a secure link plus a backup code to the captain email on file.',
        team_label: 'Team',
        choose_team: '\u2014 Choose team \u2014',
        send_code: 'Send Access Link',
        access_sent_title: 'Check the Captain Inbox',
        access_sent_copy: 'We sent a secure link and a backup code for <strong>{team}</strong>. The link opens the team profile directly, and the code is the fallback option.',
        access_info_title: 'What You Can Edit',
        access_info_copy: 'Once inside, captains can update the team name, refresh captain contact details, add or remove players, and upload a square team badge that fits the public site.',
        access_chip_profile: 'Team profile',
        access_chip_roster: 'Roster updates',
        access_chip_logo: 'Badge upload',
        msg_select_team: 'Please select a team.',
        msg_team_not_found: 'Team not found.',
        msg_email_fail: 'Failed to send email. Please try again or contact the organizer.',
        msg_code_sent: 'Access link sent to {email}',
        msg_session_expired: 'Session expired. Please start over.',
        msg_enter_code: 'Please enter the access code.',
        msg_no_code: 'No code has been generated. Please start over.',
        msg_wrong_code: 'Incorrect code. Please check your email and try again.',
        msg_session_invalid: 'Session invalid. Please authenticate again.',
        msg_roster_saved: 'Roster updated successfully!',
        msg_profile_saved: 'Team profile updated successfully!',
        msg_link_invalid: 'This access link is invalid or has expired.',
        msg_min_players: 'Keep at least 6 players on the roster.',
        msg_profile_team: 'Team name is required.',
        msg_profile_captain: 'Captain name is required.',
        msg_profile_email: 'Captain email is required.',
        msg_profile_phone: 'Captain phone is required.',
        msg_profile_player_name: 'Each player needs both a first and last name.',
        msg_profile_team_conflict: 'Another team already uses this name.',
        msg_profile_email_conflict: 'Another team already uses this captain email.',
        msg_profile_phone_conflict: 'Another team already uses this captain phone number.',
        msg_select_file: 'Please select an image file.',
        msg_file_too_large: 'File too large. Maximum size is 5 MB.',
        msg_file_type: 'Only PNG, JPEG, or WebP images are allowed.',
        msg_logo_saved: 'Logo uploaded successfully!',
      },
      nav_home:      'Home',
      nav_match:     'Match Centre',
      nav_match_tip: 'Available during the tournament',
      nav_faq:       'FAQ',
      nav_gallery:   'Gallery',
      nav_roster:    'Team Profile',
      nav_register:  'Join Tournament',
      nav: {
        tournament_hub: 'Tournament Hub',
        teams: 'Teams',
        match_centre: 'Match Centre'
      },
      footer_nav: 'Navigation',
      footer_documents: 'Documents',
      footer_connect: 'Connect',
      footer_about: 'About',
      footer_identity: 'Pocket Aces Sport Club — community-run volleyball club organizing local tournaments and events.',
      site_identity: 'Pocket Aces Sport Club — community-run volleyball club organizing local tournaments and events.',
      reg_step1:     'Details',
      reg_step2:     'Media',
      reg_step3:     'Roster',
      reg_title:     'Active Registration',
      reg_subtitle:  'Lumumby<br>Cup&nbsp;2',
      reg_desc:      'Registration is open for Pocket Aces Lumumby Cup 2. We are taking 8 teams for the new outdoor event, so secure your spot before June 3.',
      reg_fact1_title: '8 Spots',
      reg_fact1_copy: 'Compact field, quick bracket, and no long wait between meaningful matches.',
      reg_fact2_title: 'June 3',
      reg_fact2_copy: 'Registration closes on June 3, so late roster decisions need to happen now.',
      reg_fact3_title: 'Captain Flow',
      reg_fact3_copy: 'Badge, roster, and contact edits stay open through the team profile link.',
      reg_access_title: 'Need changes later?',
      reg_access_copy: 'After confirmation, captains can still update the team badge and roster from the profile page until registration closes on June 3.',
      reg_access_cta: 'Open captain profile',
      reg_identity:  'Team Details',
      reg_team_name: 'Team Name',
      reg_team_ph:   'e.g. Warsaw Eagles',
      reg_league:    'League Level',
      reg_1st:       '1st Liga',
      reg_2nd:       '2nd Liga',
      reg_3rd:       '3rd Liga',
      reg_indep:     'Independent Team',
      reg_ig:        'Instagram Handle',
      reg_ig_ph:     'yourteam',
      reg_next1:     'Next: Media',
      reg_captain:   'Captain Details',
      reg_fullname:  'Full Name',
      reg_fullname_ph: 'e.g. Jan Kowalski',
      reg_phone:     'Phone Number',
      reg_phone_ph:  '+48 123 456 789',
      reg_email:     'Email Address',
      reg_email_ph:  'captain@yourteam.com',
      reg_next2:     'Next: Roster',
      reg_back:      'Back',
      reg_media:     'Badge & Entrance Song',
      reg_roster:    'Team Roster',
      reg_hint:      'Minimum 6 players required',
      reg_note:      '<strong>Important:</strong><br>Captain must be listed as one of the players below.<br><br>Finish roster edits before June 3. This event is played outdoors, so in case of bad weather the tournament may be postponed and captains will be notified directly.',
      reg_first:     'First Name',
      reg_last:      'Last Name',
      reg_jersey:    '#',
      reg_add:       '+ Add Player',
      reg_logo_title: 'Team Badge (optional)',
      reg_logo_copy: 'Add a square logo now or skip it and upload later from the captain profile.',
      reg_song_title: 'Entrance Song (optional)',
      reg_song_copy: 'Choose a SoundCloud track to play a 15-second clip when your team walks onto the court.',
      reg_logo_drop: 'Drop a PNG, JPG, or WebP badge here',
      reg_logo_hint: 'Up to 5 MB. Square badges look best.',
      reg_logo_skip: 'Optional. You can also add this later.',
      reg_logo_remove: 'Remove badge',
      reg_choose_file: 'Choose File',
      reg_terms:     'I have read and accept the <a href="/static/assets/documents/Regulations_english_czerwec.pdf" target="_blank">tournament regulations</a>',
      reg_age:       'All players are 18 years of age or older',
        reg_parental:  'If any player is under 18, a <a href="/static/assets/documents/ZGODA_RODZICA_Pocket_Aces_12_04_2026_1.pdf" target="_blank">parental consent form</a> must be filled out and provided at registration.',
      reg_photo:     'I consent to photos/videos being taken during the event',
      reg_payment:   'I understand the entry fee is <strong>150 zł</strong> and payment details plus the payment deadline will be sent by email',
      reg_submit:    'Join Tournament',
      reg_success:   'Registration Sent!',
      reg_success_txt: 'Your team has been submitted for Pocket Aces Lumumby Cup 2. Payment details and the deadline will be sent to your email address shortly.',
      // Validation
      err_team_name: 'Team name is required.',
      err_league:    'Please select a league level.',
      err_fullname:  'Please enter first and last name.',
      err_phone:     'Phone number is required.',
      err_email:     'Please enter a valid email address.',
      err_players:   'At least 6 players are required (currently {n}).',
      err_logo_type: 'Only PNG, JPEG, or WebP logos are allowed.',
      err_logo_size: 'Logo file is too large. Maximum size is 5 MB.',
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
        label: '6 czerwca • 09:00 • Boisko przy akademiku nr 8',
        title: {
          intro_top: 'POCKET',
          intro_bottom: 'ACES',
          final_top: 'LUMUMBY',
          final_bottom: 'CUP 2'
        },
        text: 'Rejestracja na Pocket Aces Lumumby Cup 2 jest otwarta. Gramy na zewnętrznym boisku, limit to 8 drużyn, a pierwszy gwizdek o 09:00. Zapisz ekipę przed końcem rejestracji 3 czerwca.',
        mobile_fact1: 'Dzień Turnieju',
        mobile_fact2: 'Limit Drużyn',
        mobile_fact3: 'Boisko Outdoor',
        price: { label: 'za drużynę' },
        counter: { label: 'Zarejestrowane drużyny' },
        cta: 'Zapisz się',
        closed: 'Rejestracja zamknięta'
      },
      voting: {
        title: 'Ulubieńcy Publiczności',
        subtitle: 'Najpopularniejsza Drużyna',
        count: 'Głosów',
        cta: 'Głosuj'
      },
      deal: {
        heading: 'Dlaczego warto',
        card1: {
          title: 'Nagrody',
          text: 'Na koniec czekają puchary i medale — wszystko rozstrzyga się na boisku w walce o najwyższe miejsca. Kibice mogą głosować na najlepszą drużynę na stronie, a zespół z największą liczbą głosów otrzyma specjalne nagrody.',
          list1: 'Puchary i medale',
          list2: 'Głosowanie kibiców',
          list3: 'Specjalne nagrody'
        },
        card2: {
          title: 'Rejestracja',
          text: 'Zapisy trwają i tylko 8 drużyn wejdzie do turnieju. Zabezpiecz miejsce, zanim minie deadline.',
          list1: 'Deadline: 3 czerwca',
          list2: 'Wpisowe: 150 zł'
        },
        card3: {
          title: 'Dzień turnieju open air',
          text: 'Spotykamy się 6 czerwca o 09:00 na zewnętrznym boisku przy akademiku nr 8 na cały dzień grania.',
          list1: 'Boisko przy akademiku nr 8',
          list2: 'Przyjazd 30-60 min wcześniej'
        },
        card4: {
          title: 'Pogoda',
          text: 'To wydarzenie plenerowe. Jeśli pogoda będzie zła, turniej może zostać przełożony, a kapitanowie dostaną informację bezpośrednio.',
          list1: 'Format outdoor',
          list2: 'Aktualizacje dla kapitanów'
        }
      },
      deal_lead: 'Kompaktowy turniej open-air dla ekip, które chcą czytelnego rytmu dnia, jasnej stawki i lepszej atmosfery meczowej.',
      location: {
        kicker: 'Szczegóły obiektu',
        title: 'Obiekt',
        text: 'Pocket Aces Lumumby Cup 2 gramy na zewnętrznym boisku przy akademiku nr 8 w Łodzi. Przyjedź z drużyną 30-60 minut wcześniej na rejestrację i rozgrzewkę.',
        info: { label: 'Lokalizacja', value: 'Strajku Łódzkich Studentów 1981 r. 2, 91-404 Łódź' },
        date: { label: 'Data', value: '6 czerwca, 09:00' },
        link: 'Zobacz na Google Maps'
      },
      location_pill1_title: 'Open-Air Setup',
      location_pill1_copy: 'Świeże powietrze, jedno skupione boisko i turniejowy rytm, który trzyma tempo od rana do ostatniego gwizdka.',
      location_pill2_title: 'Prosta Logistyka',
      location_pill2_copy: 'Szybki dojazd, prosty kontakt z kapitanami i układ miejsca, który nie spowalnia dnia.',
      location_pill3_title: 'Płynny Rytm Meczów',
      location_pill3_copy: 'Krótkie przerwy, czytelna przestrzeń przy linii i układ, który pozwala utrzymać tempo każdej rundy.',
      registered: {
        cta: 'Zobacz drużyny ->',
        modal_title: 'Zarejestrowane Drużyny',
        modal_subtitle: 'Pocket Aces Lumumby Cup 2',
        col_team: 'Drużyna',
        col_captain: 'Kapitan',
        col_level: 'Poziom',
        empty: 'Brak zarejestrowanych drużyn.'
      },
      arena: { heading: 'Obiekt' },
      arena_note: 'Czystsza sceneria open-air, kompaktowe otoczenie i atmosfera, która sprawia, że cały dzień czuje się jak prawdziwe wydarzenie.',
      // Road to Victory
      road: {
        heading: 'Harmonogram zapisów',
        lead: 'Od zapisu do pierwszego gwizdka: te cztery momenty budują cały tydzień turniejowy.',
        step1: { date: 'Teraz', title: 'Zapisy otwarte', desc: 'Rejestracja drużyn trwa. Dołącz zanim zniknie 8 miejsc.' },
        step2: { date: '3 czerwca', title: 'Koniec rejestracji', desc: 'Ostateczny termin na zgłoszenie drużyny do turnieju.' },
        step3: { date: 'Po zamknięciu', title: 'Info dla kapitanów', desc: 'Szczegóły organizacyjne wydarzenia trafią do zapisanych kapitanów.' },
        step4: { date: '06.06, 09:00', title: 'Dzień turnieju', desc: 'Pocket Aces Lumumby Cup 2 startuje na boisku przy akademiku nr 8.' }
      },
      // FAQ page
      faq: {
        title: 'FAQ',
        q1: 'Co jeśli zawodnik ma mniej niż 18 lat?',
        a1: 'Jeśli którykolwiek z zawodników ma mniej niż 18 lat, należy wysłać <a href="/static/assets/documents/ZGODA_RODZICA_Pocket_Aces_12_04_2026_1.pdf" target="_blank">zgodę rodzica</a> przed wydarzeniem i dostarczyć ją w wersji papierowej w dniu turnieju.',
        q2: 'Co jeśli drużyna nie ma strojów?',
        a2: 'Numery na koszulkach nie są wymagane. Jednolite stroje są mile widziane, ale najważniejsze jest to, żeby drużynę dało się łatwo rozpoznać na boisku.',
        q3: 'Czy można otrzymać zwrot opłaty?',
        a3: 'Jeśli turniej zostanie odwołany z powodu zbyt małej liczby drużyn, wszystkie wpłaty są zwracane w ciągu 7 dni.',
        q4: 'Co jeśli pogoda będzie zła?',
        a4: 'Ponieważ to wydarzenie open-air, turniej może zostać przełożony w przypadku złej pogody. Zarejestrowani kapitanowie dostaną informację bezpośrednio.',
        q5: 'Ilu zawodników może być w drużynie?',
        a5: 'Do rozpoczęcia meczu potrzebujesz 6 zawodników na boisku, a rezerwowych możesz zgłosić bez limitu.',
        q6: 'Czy można zmienić zawodnika po rejestracji?',
        a6: 'Zmiany w składzie są akceptowane tylko do końca rejestracji 3 czerwca. Po starcie turnieju nie można już zmieniać rosteru.',
        q7: 'Gdzie znajdziemy harmonogram meczów?',
        a7: 'Ostateczny format zależy od liczby zgłoszonych drużyn. Kapitanowie dostaną aktualizacje bezpośrednio, a najważniejsze informacje o harmonogramie pojawią się też na stronie.',
        ask_title: 'Zadaj pytanie',
        ask_email_ph: 'Twój email',
        ask_question_ph: 'Twoje pytanie',
        ask_btn: 'Wyślij',
        ask_success: 'Pytanie wysłane!'
      },
      cs: {
        heading: 'Match Centre wkrótce',
        sub: 'Match Centre rusza <strong>6 czerwca o 09:00</strong>. Do tego czasu wykorzystaj odliczanie, żeby zapisać drużynę na Pocket Aces Lumumby Cup 2.',
        days: 'Dni',
        hours: 'Godz',
        min: 'Min',
        sec: 'Sek',
        live: 'Dzień turnieju już trwa.',
        reloading: 'Do zobaczenia na boisku.',
        groups_heading: 'Grupy',
        roster_btn: 'Zapisz się',
        back: 'Wróć na stronę główną',
      },
      rp: {
        title: 'Dostep do profilu druzyny',
        heading: 'Zarzadzaj <span>druzyna</span>',
        subtitle: 'Kapitan moze w jednym miejscu zaktualizowac sklad, herb i dane kontaktowe.',
        logo_title: 'Herb druzyny',
        logo_copy: 'Wgraj lub podmien kwadratowy herb. Najlepiej sprawdzi sie PNG, JPG albo WebP do 5 MB.',
        logo_drop: 'Upusc kwadratowy herb tutaj lub wybierz plik',
        logo_hint: 'Opcjonalne, ale polecane do publicznej prezentacji druzyny.',
        logo_empty: 'Brak herbu',
        choose_file: 'Wybierz plik',
        no_file: 'Nie wybrano pliku',
        upload_logo: 'Prześlij logo',
        profile_title: 'Dane druzyny',
        profile_copy: 'Te dane sa wykorzystywane do kontaktu, potwierdzen platnosci i publicznej prezentacji druzyny.',
        profile_subtitle: 'Pilnuj, aby przed dniem turnieju sklad, kontakt i herb byly aktualne.',
        team_name: 'Nazwa druzyny',
        captain_name: 'Imie i nazwisko kapitana',
        captain_email: 'Email kapitana',
        captain_phone: 'Telefon kapitana',
        roster_title: 'Sklad',
        roster_subtitle: 'Zostaw co najmniej 6 zawodnikow. Mozesz dodawac i usuwac graczy przed wydarzeniem.',
        roster_rule: 'Zostaw co najmniej 6 zawodnikow w skladzie.',
        player_first: 'Imie',
        player_first_ph: 'Imie',
        player_last: 'Nazwisko',
        player_last_ph: 'Nazwisko',
        player_remove: 'Usun',
        players_chip: 'zawodnikow',
        add_player: 'Dodaj zawodnika',
        save_profile: 'Zapisz zmiany',
        start_over: 'Wybierz inna druzyne',
        save: 'Zapisz skład',
        cancel: 'Anuluj',
        enter_code: 'Uzyj kodu zapasowego',
        code_hint: 'Na email kapitana wyslalismy tez kod zapasowy. Jesli link nie zadziala, wpisz go tutaj.',
        access_code_label: 'Kod dostępu',
        code_ph: 'Wpisz kod zapasowy',
        verify: 'Zweryfikuj kod',
        back: 'Wstecz',
        select_team: 'Wybierz druzyne',
        select_hint: 'Wybierz swoja druzyne, a wyslemy bezpieczny link oraz kod zapasowy na email kapitana.',
        team_label: 'Drużyna',
        choose_team: '— Wybierz drużynę —',
        send_code: 'Wyslij link dostepu',
        access_sent_title: 'Sprawdz skrzynke kapitana',
        access_sent_copy: 'Wyslalismy bezpieczny link oraz kod zapasowy dla <strong>{team}</strong>. Link otwiera profil druzyny od razu, a kod jest planem awaryjnym.',
        access_info_title: 'Co mozna edytowac',
        access_info_copy: 'Po zalogowaniu kapitan moze zmienic nazwe druzyny, dane kontaktowe, sklad oraz wgrac kwadratowy herb pasujacy do publicznej strony.',
        access_chip_profile: 'Profil druzyny',
        access_chip_roster: 'Aktualizacje skladu',
        access_chip_logo: 'Wgrywanie herbu',
        msg_select_team: 'Proszę wybrać drużynę.',
        msg_team_not_found: 'Nie znaleziono drużyny.',
        msg_email_fail: 'Nie udało się wysłać e-maila. Spróbuj ponownie lub skontaktuj się z organizatorem.',
        msg_code_sent: 'Link dostepu wyslany na {email}',
        msg_session_expired: 'Sesja wygasła. Zacznij od nowa.',
        msg_enter_code: 'Proszę wpisać kod dostępu.',
        msg_no_code: 'Kod nie został wygenerowany. Zacznij od nowa.',
        msg_wrong_code: 'Nieprawidłowy kod. Sprawdź e-mail i spróbuj ponownie.',
        msg_session_invalid: 'Sesja nieprawidłowa. Zaloguj się ponownie.',
        msg_roster_saved: 'Skład został zaktualizowany!',
        msg_profile_saved: 'Profil druzyny zostal zaktualizowany!',
        msg_link_invalid: 'Ten link jest nieprawidlowy albo wygasl.',
        msg_min_players: 'Zostaw co najmniej 6 zawodnikow w skladzie.',
        msg_profile_team: 'Nazwa druzyny jest wymagana.',
        msg_profile_captain: 'Imie i nazwisko kapitana sa wymagane.',
        msg_profile_email: 'Email kapitana jest wymagany.',
        msg_profile_phone: 'Telefon kapitana jest wymagany.',
        msg_profile_player_name: 'Kazdy zawodnik musi miec imie i nazwisko.',
        msg_profile_team_conflict: 'Inna druzyna uzywa juz tej nazwy.',
        msg_profile_email_conflict: 'Inna druzyna uzywa juz tego emaila kapitana.',
        msg_profile_phone_conflict: 'Inna druzyna uzywa juz tego numeru telefonu kapitana.',
        msg_select_file: 'Proszę wybrać plik obrazu.',
        msg_file_too_large: 'Plik za duży. Maksymalny rozmiar to 5 MB.',
        msg_file_type: 'Dozwolone tylko pliki PNG, JPEG lub WebP.',
        msg_logo_saved: 'Logo zostało przesłane!',
      },
      nav_home:      'Strona Główna',
      nav_match:     'Centrum Meczy',
      nav_match_tip: 'Dostępne podczas turnieju',
      nav_faq:       'FAQ',
      nav_gallery:   'Galeria',
      nav_roster:    'Profil druzyny',
      nav_register:  'Zapisz się',
      gallery_page: {
        eyebrow: 'Pocket Aces',
        title: 'Galeria',
        subtitle: 'Zdjęcia i skróty wideo z Pocket Aces Lumumby Cup 2.',
        photos_title: 'Zdjęcia',
        videos_title: 'Skróty Wideo',
        prev_title: 'Poprzedni Turniej',
        prev_subtitle: 'Archiwum Mediów',
        empty: 'Galeria zostanie zaktualizowana po rozpoczęciu Pocket Aces Lumumby Cup 2.'
      },
      nav: {
        tournament_hub: 'Centrum turnieju',
        teams: 'Drużyny',
        match_centre: 'Centrum Meczowe'
      },
      footer_nav: 'Nawigacja',
      footer_documents: 'Dokumenty',
      footer_connect: 'Kontakt',
      footer_about: 'O nas',
      footer_identity: 'Pocket Aces Sport Club — lokalny klub siatkówki organizujący turnieje i wydarzenia.',
      site_identity: 'Pocket Aces Sport Club — lokalny klub siatkówki organizujący turnieje i wydarzenia.',
      reg_step1:     'Dane',
      reg_step2:     'Media',
      reg_step3:     'Skład',
      reg_title:     'Aktywna Rejestracja',
      reg_subtitle:  'Lumumby<br>Cup&nbsp;2',
      reg_desc:      'Rejestracja na Pocket Aces Lumumby Cup 2 jest otwarta. Bierzemy 8 drużyn na nowe wydarzenie outdoorowe, więc zapisz skład przed 3 czerwca.',
      reg_fact1_title: '8 Miejsc',
      reg_fact1_copy: 'Kompaktowa stawka, szybka drabinka i bez długiego czekania między ważnymi meczami.',
      reg_fact2_title: '3 Czerwca',
      reg_fact2_copy: 'Rejestracja zamyka się 3 czerwca, więc decyzje o składzie trzeba domknąć teraz.',
      reg_fact3_title: 'Captain Flow',
      reg_fact3_copy: 'Herb, skład i dane kontaktowe dalej można poprawiać z poziomu profilu drużyny.',
      reg_access_title: 'Chcesz coś zmienić później?',
      reg_access_copy: 'Po zapisaniu drużyny kapitan nadal może zaktualizować herb i skład w profilu do końca rejestracji 3 czerwca.',
      reg_access_cta: 'Otwórz profil kapitana',
      reg_identity:  'Dane drużyny',
      reg_team_name: 'Nazwa Drużyny',
      reg_team_ph:   'np. Warsaw Eagles',
      reg_league:    'Poziom Ligi',
      reg_1st:       '1 Liga',
      reg_2nd:       '2 Liga',
      reg_3rd:       '3 Liga',
      reg_indep:     'Drużyna Niezależna',
      reg_ig:        'Instagram',
      reg_ig_ph:     'twojadruzyna',
      reg_next1:     'Dalej: Media',
      reg_captain:   'Dane Kapitana',
      reg_fullname:  'Imię i Nazwisko',
      reg_fullname_ph: 'np. Jan Kowalski',
      reg_phone:     'Telefon',
      reg_phone_ph:  '+48 123 456 789',
      reg_email:     'E-mail',
      reg_email_ph:  'kapitan@twojadruzyna.com',
      reg_next2:     'Dalej: Skład',
      reg_back:      'Wstecz',
      reg_media:     'Herb i piosenka wejścia',
      reg_roster:    'Skład Drużyny',
      reg_hint:      'Minimum 6 zawodników',
      reg_note:      '<strong>Ważne:</strong><br>Kapitan musi być wpisany jako jeden z zawodników poniżej.<br><br>Zakończ zmiany w składzie do 3 czerwca. Turniej gramy na zewnątrz, więc w przypadku złej pogody wydarzenie może zostać przełożone, a kapitanowie dostaną informację bezpośrednio.',
      reg_first:     'Imię',
      reg_last:      'Nazwisko',
      reg_jersey:    '#',
      reg_add:       '+ Dodaj Zawodnika',
      reg_logo_title: 'Herb druzyny (opcjonalnie)',
      reg_logo_copy: 'Dodaj kwadratowe logo teraz albo pomin ten krok i wgraj je pozniej z profilu kapitana.',
      reg_song_title: 'Piosenka wejścia (opcjonalnie)',
      reg_song_copy: 'Wybierz utwór z SoundCloud, z którego odtworzy się 15-sekundowy fragment przy wejściu drużyny na boisko.',
      reg_logo_drop: 'Upusc tutaj herb PNG, JPG albo WebP',
      reg_logo_hint: 'Do 5 MB. Najlepiej wygladaja kwadratowe herby.',
      reg_logo_skip: 'Opcjonalne. Mozesz dodac je pozniej.',
      reg_logo_remove: 'Usun herb',
      reg_choose_file: 'Wybierz plik',
      reg_terms:     'Przeczytałem i akceptuję <a href="/static/assets/documents/Regulations_polish%20czerwec%20.pdf" target="_blank">regulamin turnieju</a>',
      reg_age:       'Wszyscy zawodnicy mają ukończone 18 lat',
        reg_parental:  'Jeśli którykolwiek z zawodników ma mniej niż 18 lat, należy wypełnić <a href="/static/assets/documents/ZGODA_RODZICA_Pocket_Aces_12_04_2026_1.pdf" target="_blank">zgodę rodzica</a> i dostarczyć ją organizatorom.',
      reg_photo:     'Wyrażam zgodę na zdjęcia/filmy podczas wydarzenia',
      reg_payment:   'Rozumiem, że wpisowe wynosi <strong>150 zł</strong>, a szczegóły płatności wraz z terminem zostaną przesłane e-mailem',
      reg_submit:    'Zapisz się',
      reg_success:   'Zgłoszenie wysłane!',
      reg_success_txt: 'Twoja drużyna została zgłoszona do Pocket Aces Lumumby Cup 2. Szczegóły płatności i termin zostaną wysłane na Twój adres e-mail.',
      // Validation
      err_team_name: 'Nazwa drużyny jest wymagana.',
      err_league:    'Wybierz poziom ligi.',
      err_fullname:  'Podaj imię i nazwisko.',
      err_phone:     'Telefon jest wymagany.',
      err_email:     'Podaj prawidłowy e-mail.',
      err_players:   'Wymaganych jest co najmniej 6 graczy (obecnie {n}).',
      err_logo_type: 'Dozwolone sa tylko logotypy PNG, JPEG lub WebP.',
      err_logo_size: 'Plik z logo jest za duzy. Maksymalnie 5 MB.',
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

  const MOBILE_TEXT_OVERRIDES = {
    en: {
      'hero.text': 'Registration is open for Pocket Aces Lumumby Cup 2. Outdoor play, 8 teams, first serve at 09:00. Lock your spot before registration closes on June 3.'
    },
    pl: {
      'hero.text': 'Rejestracja na Pocket Aces Lumumby Cup 2 jest otwarta. Gramy na zewnątrz, limit to 8 drużyn, a pierwszy gwizdek o 09:00. Zapisz ekipę przed końcem rejestracji 3 czerwca.'
    }
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
    const isMobile = window.matchMedia('(max-width: 767.98px)').matches;

    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      const baseValue = key.split('.').reduce((acc, k) => (acc && acc[k] !== undefined ? acc[k] : undefined), t);
      const mobileValue = MOBILE_TEXT_OVERRIDES[l] && MOBILE_TEXT_OVERRIDES[l][key];
      const value = isMobile && mobileValue !== undefined ? mobileValue : baseValue;
      if (value !== undefined) {
        // Для FAQ-ответов и специальных заметок используем innerHTML
        if (/^faq\.a\d+$/.test(key) || key === 'reg_note' || key === 'reg_parental' || key === 'reg_payment' || key === 'reg_terms' || key === 'cs.sub') {
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
  window.__PA_T = T;
  applyLang(lang);
})();
