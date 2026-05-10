// Theme management — persisted, no flash
(function(){
  const saved = localStorage.getItem('iq_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  applyTheme(next);
}
function setTheme(t) { applyTheme(t); }
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('iq_theme', t);
  // Update all theme buttons/labels on page
  document.querySelectorAll('#themeIcon').forEach(el => el.textContent = t === 'dark' ? '🌙' : '☀️');
  document.querySelectorAll('#themeLabel').forEach(el => el.textContent = t === 'dark' ? 'Dark mode' : 'Light mode');
  document.querySelectorAll('.ttg-btn').forEach(btn => {
    btn.classList.toggle('active', (t === 'dark' && btn.id === 'ttg-dark') || (t === 'light' && btn.id === 'ttg-light'));
  });
  // Redraw chart if exists
  if (window._chartInstance) { window._chartInstance.destroy(); window._chartInstance = null; }
  if (typeof renderChart === 'function' && window._lastResults) renderChart(window._lastResults);
}
function openSidebar() {
  document.getElementById('sidebar')?.classList.add('open');
  document.getElementById('sidebarOverlay')?.style && (document.getElementById('sidebarOverlay').style.display = 'block');
}
function closeSidebar() {
  document.getElementById('sidebar')?.classList.remove('open');
  const ov = document.getElementById('sidebarOverlay');
  if (ov) ov.style.display = '';
}
