(() => {
  const root = document.documentElement;
  const body = document.body;
  const storageKey = 'diario-escolar-pro-theme';

  function applyTheme(theme) {
    const selected = theme === 'dark' ? 'dark' : 'light';
    root.dataset.theme = selected;
    try { localStorage.setItem(storageKey, selected); } catch (_) {}
    document.querySelectorAll('[data-theme-label]').forEach(el => {
      el.textContent = selected === 'dark' ? 'Modo claro' : 'Modo escuro';
    });
  }

  let saved = null;
  try { saved = localStorage.getItem(storageKey); } catch (_) {}
  if (!saved && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) saved = 'dark';
  applyTheme(saved || 'light');

  document.addEventListener('click', event => {
    const theme = event.target.closest('[data-theme-toggle]');
    if (theme) applyTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');

    const open = event.target.closest('[data-nav-open]');
    if (open) body.classList.add('nav-open');

    const close = event.target.closest('[data-nav-close]');
    if (close) body.classList.remove('nav-open');
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') body.classList.remove('nav-open');
  });

  function normalizePath(value) {
    try { return (new URL(value, location.origin).pathname || '/').replace(/\/$/, '') || '/'; }
    catch (_) { return String(value || '').split('?')[0].split('#')[0].replace(/\/$/, '') || '/'; }
  }

  const current = normalizePath(location.pathname).toLowerCase();
  let best = null, score = -1;
  document.querySelectorAll('.sidebar a[href]').forEach(a => {
    a.classList.remove('active');
    a.removeAttribute('aria-current');
    const custom = (a.dataset.activePaths || '').split('|').filter(Boolean);
    const paths = custom.length ? custom : [a.getAttribute('href')];
    paths.forEach(raw => {
      const p = normalizePath(raw).toLowerCase();
      const match = p === '/' ? current === '/' : (current === p || current.startsWith(p + '/'));
      if (match) {
        const currentScore = p.length + (current === p ? 1000 : 0);
        if (currentScore > score) { best = a; score = currentScore; }
      }
    });
  });
  if (best) { best.classList.add('active'); best.setAttribute('aria-current', 'page'); }

  document.querySelectorAll('[data-table-filter]').forEach(input => {
    const selector = input.getAttribute('data-table-filter');
    const table = selector ? document.querySelector(selector) : null;
    if (!table) return;
    input.addEventListener('input', () => {
      const q = input.value.trim().toLocaleLowerCase('pt-BR');
      table.querySelectorAll('tbody tr').forEach(row => {
        row.hidden = q && !row.textContent.toLocaleLowerCase('pt-BR').includes(q);
      });
    });
  });

  if ('serviceWorker' in navigator && location.protocol === 'https:') {
    window.addEventListener('load', () => navigator.serviceWorker.register('/service-worker.js', { scope: '/' }).catch(() => {}));
  }
})();
