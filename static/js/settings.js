/* Settings page logic */
document.addEventListener('DOMContentLoaded', () => {
  loadUserData();
  applyTheme(localStorage.getItem('iq_theme') || 'dark');
  loadPrefs();
  updateThemeButtons();
});

function loadUserData() {
  const d = localStorage.getItem('iq_user');
  const u = d ? JSON.parse(d) : {};
  const [fname, ...lname] = (u.name || '').split(' ');
  setVal('sf-fname', fname || '');
  setVal('sf-lname', lname.join(' ') || '');
  setVal('sf-email', u.email || '');
  setVal('sf-company', u.company || '');
  const ini = (u.name || u.email || 'G')[0].toUpperCase();
  document.getElementById('userAvatar').textContent = ini;
  document.getElementById('bigAvatar').textContent = ini;
  document.getElementById('userName').textContent = u.name || 'Guest';
  document.getElementById('avName').textContent = u.name || 'Guest User';
  document.getElementById('avRole').textContent = u.role === 'influencer' ? 'Creator / Influencer' : 'Brand Marketer';
}

function loadPrefs() {
  const prefs = JSON.parse(localStorage.getItem('iq_prefs') || '{}');
  const setCheck = (id, def) => { const el = document.getElementById(id); if (el) el.checked = prefs[id] !== undefined ? prefs[id] : def; };
  const setSelectVal = (id, def) => { const el = document.getElementById(id); if (el && prefs[id]) el.value = prefs[id]; };
  setCheck('pref-autodemo', false);
  setCheck('pref-fraud', true);
  setCheck('pref-explain', true);
  setSelectVal('pref-currency', 'USD');
  setSelectVal('pref-results', '12');
  setSelectVal('pref-platform', '');
  setSelectVal('sf-currency', 'USD');
}

function setVal(id, v) { const el = document.getElementById(id); if (el) el.value = v; }

function showTab(name) {
  document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.sn-item').forEach(i => i.classList.remove('active'));
  document.getElementById('tab-' + name)?.classList.add('active');
  event.currentTarget.classList.add('active');
}

function saveProfile() {
  const fname   = document.getElementById('sf-fname').value.trim();
  const lname   = document.getElementById('sf-lname').value.trim();
  const email   = document.getElementById('sf-email').value.trim();
  const company = document.getElementById('sf-company').value.trim();
  const bio     = document.getElementById('sf-bio').value.trim();
  const cur     = document.getElementById('sf-currency').value;
  if (!email) { showStatus('profileStatus', '⚠ Email is required', true); return; }
  const d = localStorage.getItem('iq_user');
  const u = d ? JSON.parse(d) : {};
  u.name = `${fname} ${lname}`.trim() || u.name;
  u.email = email; u.company = company; u.bio = bio;
  localStorage.setItem('iq_user', JSON.stringify(u));
  savePref('currency', cur);
  localStorage.setItem('iq_pref_currency', cur);
  loadUserData();
  showStatus('profileStatus', '✓ Changes saved');
}

function savePassword() {
  const cur  = document.getElementById('ac-curpw').value;
  const nw   = document.getElementById('ac-newpw').value;
  const conf = document.getElementById('ac-confpw').value;
  if (!cur) { showStatus('pwStatus', '⚠ Enter current password', true); return; }
  if (nw.length < 8) { showStatus('pwStatus', '⚠ Min 8 characters', true); return; }
  if (nw !== conf) { showStatus('pwStatus', '⚠ Passwords do not match', true); return; }
  showStatus('pwStatus', '✓ Password updated');
}

function savePref(key, val) {
  const prefs = JSON.parse(localStorage.getItem('iq_prefs') || '{}');
  prefs[key] = val;
  localStorage.setItem('iq_prefs', JSON.stringify(prefs));
  const s = document.createElement('span');
  s.className = 'save-status'; s.textContent = '✓ Saved';
  s.style.cssText = 'position:fixed;bottom:24px;right:24px;background:rgba(34,197,94,.9);color:#fff;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;z-index:999';
  document.body.appendChild(s);
  setTimeout(() => s.remove(), 1500);
}

function showStatus(id, msg, isErr) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.style.color = isErr ? 'var(--red)' : 'var(--green)';
  setTimeout(() => el.textContent = '', 2500);
}

function updateThemeButtons() {
  const t = document.documentElement.getAttribute('data-theme');
  document.getElementById('ttg-dark')?.classList.toggle('active', t === 'dark');
  document.getElementById('ttg-light')?.classList.toggle('active', t === 'light');
}

function setTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('iq_theme', t);
  updateThemeButtons();
  document.querySelectorAll('#themeIcon').forEach(el => el.textContent = t === 'dark' ? '🌙' : '☀️');
  document.querySelectorAll('#themeLabel').forEach(el => el.textContent = t === 'dark' ? 'Dark mode' : 'Light mode');
  savePref('theme', t);
}

function toggleTheme() {
  const t = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  setTheme(t);
}

function exportData() {
  const data = { user: JSON.parse(localStorage.getItem('iq_user')||'{}'), prefs: JSON.parse(localStorage.getItem('iq_prefs')||'{}'), exportDate: new Date().toISOString() };
  const blob = new Blob([JSON.stringify(data, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'influenceiq_data.json';
  a.click();
}

function confirmDelete() {
  if (confirm('This will permanently delete your account. This action cannot be undone. Continue?')) {
    localStorage.removeItem('iq_user');
    localStorage.removeItem('iq_prefs');
    window.location.href = '/';
  }
}

function confirmLogout() {
  const d = localStorage.getItem('iq_user');
  if (d) { const u = JSON.parse(d); u.loggedIn = false; localStorage.setItem('iq_user', JSON.stringify(u)); }
  window.location.href = '/';
}

function copyApiKey() {
  const val = document.getElementById('apiKeyInput').value;
  navigator.clipboard.writeText(val).then(() => showStatus('', ''));
  alert('API key copied to clipboard!');
}

function toggleApiKey() {
  const inp = document.getElementById('apiKeyInput');
  inp.type = inp.type === 'password' ? 'text' : 'password';
}
