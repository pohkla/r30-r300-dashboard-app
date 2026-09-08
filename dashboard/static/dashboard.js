(() => {
  const rows = document.querySelectorAll('.clickable-row[data-href]');

  const shouldIgnore = (target) => Boolean(target.closest('a, button, input, select, textarea, label, form'));

  rows.forEach((row) => {
    row.addEventListener('click', (event) => {
      if (shouldIgnore(event.target)) return;
      window.location.href = row.dataset.href;
    });

    row.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      if (shouldIgnore(event.target)) return;
      event.preventDefault();
      window.location.href = row.dataset.href;
    });
  });
})();
