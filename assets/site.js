/* Progressive enhancement: every publication and page is readable without JavaScript. */
(() => {
  const menuButton = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.site-nav');
  document.documentElement.classList.add('js');
  if (menuButton && nav) {
    menuButton.hidden = false;
    const closeMenu = () => {
      menuButton.setAttribute('aria-expanded', 'false');
      nav.dataset.open = 'false';
    };
    menuButton.addEventListener('click', () => {
      const open = menuButton.getAttribute('aria-expanded') !== 'true';
      menuButton.setAttribute('aria-expanded', String(open));
      nav.dataset.open = String(open);
    });
    nav.addEventListener('click', (event) => {
      if (event.target.closest('a')) closeMenu();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape') return;
      document.querySelectorAll('.nav-more[open]').forEach((item) => { item.open = false; });
      if (menuButton.getAttribute('aria-expanded') === 'true') {
        closeMenu();
        menuButton.focus();
      }
    });
    document.addEventListener('click', (event) => {
      document.querySelectorAll('.nav-more[open]').forEach((item) => {
        if (!item.contains(event.target)) item.open = false;
      });
      if (!event.target.closest('.site-header')) closeMenu();
    });
    window.matchMedia('(min-width: 901px)').addEventListener('change', closeMenu);
  }

  const filters = document.querySelector('[data-publication-filters]');
  if (!filters) return;
  const search = document.querySelector('#publication-search');
  const year = document.querySelector('#publication-year');
  const topic = document.querySelector('#publication-topic');
  const chips = [...document.querySelectorAll('[data-type-filter]')];
  const papers = [...document.querySelectorAll('[data-publication]')];
  const groups = [...document.querySelectorAll('[data-publication-group]')];
  const sections = [...document.querySelectorAll('[data-publication-section]')];
  const result = document.querySelector('#publication-results');
  const empty = document.querySelector('#publication-empty');
  let type = 'all';
  const normalize = (text) => text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  papers.forEach((paper) => {
    paper.dataset.search = normalize(paper.dataset.search);
  });

  const apply = () => {
    const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    let count = 0;
    papers.forEach((paper) => {
      const matches = words.every((word) => paper.dataset.search.includes(word))
        && (year.value === 'all' || paper.dataset.year === year.value)
        && (topic.value === 'all' || paper.dataset.topics.split(' ').includes(topic.value))
        && (type === 'all' || type.split(',').includes(paper.dataset.type));
      paper.hidden = !matches;
      if (matches) count++;
    });
    groups.forEach((group) => { group.hidden = !group.querySelector('[data-publication]:not([hidden])'); });
    sections.forEach((section) => { section.hidden = !section.querySelector('[data-publication]:not([hidden])'); });
    chips.forEach((chip) => { chip.setAttribute('aria-pressed', String(chip.dataset.typeFilter === type)); });
    result.textContent = `${count} of ${papers.length} publications`;
    empty.hidden = count !== 0;
    const params = new URLSearchParams();
    if (search.value.trim()) params.set('q', search.value.trim());
    if (year.value !== 'all') params.set('year', year.value);
    if (topic.value !== 'all') params.set('topic', topic.value);
    if (type !== 'all') params.set('type', type);
    const query = params.toString();
    const next = `${location.pathname}${query ? `?${query}` : ''}${location.hash}`;
    if (`${location.pathname}${location.search}${location.hash}` !== next) history.replaceState(null, '', next);
  };
  const readUrl = () => {
    const params = new URLSearchParams(location.search);
    search.value = params.get('q') || '';
    year.value = [...year.options].some((option) => option.value === params.get('year')) ? params.get('year') : 'all';
    topic.value = [...topic.options].some((option) => option.value === params.get('topic')) ? params.get('topic') : 'all';
    type = chips.some((chip) => chip.dataset.typeFilter === params.get('type')) ? params.get('type') : 'all';
    apply();
  };
  filters.hidden = false;
  readUrl();
  search.addEventListener('input', apply);
  year.addEventListener('change', apply);
  topic.addEventListener('change', apply);
  chips.forEach((chip) => chip.addEventListener('click', () => { type = chip.dataset.typeFilter; apply(); }));
  document.querySelector('#publication-reset').addEventListener('click', () => {
    search.value = '';
    year.value = 'all';
    topic.value = 'all';
    type = 'all';
    apply();
    search.focus();
  });
  window.addEventListener('popstate', readUrl);
})();
