/* ============================================================
   SCRIBAL FINGERPRINTS — Shared JS
   Navigation, utilities
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  // --- Mobile nav toggle ---
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
    });
  }

  // --- Active nav highlighting ---
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(a => {
    const href = a.getAttribute('href');
    if (href === currentPage) {
      a.classList.add('active');
    }
  });

  // --- Tab switching ---
  document.querySelectorAll('.tab-bar').forEach(bar => {
    bar.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.tab;
        const container = bar.closest('.tab-container') || bar.parentElement;

        bar.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        container.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        const panel = container.querySelector(`#${target}`);
        if (panel) panel.classList.add('active');
      });
    });
  });
});
