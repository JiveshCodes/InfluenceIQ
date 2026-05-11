/* InfluenceIQ v2 — Dashboard Logic */

const RATES   = { USD:1, INR:83.5, EUR:0.92, GBP:0.79, CAD:1.36, AED:3.67 };
const SYMBOLS = { USD:'$', INR:'₹', EUR:'€', GBP:'£', CAD:'C$', AED:'AED ' };
const SUBCATS = {
  Fashion:   ['Streetwear','Luxury fashion','Ethnic wear','Sustainable fashion'],
  Sports:    ['Cricket','Football','Fitness training','Outdoor adventure'],
  Tech:      ['Smartphones','AI/ML','Gaming','Software development'],
  Lifestyle: ['Travel','Food','Daily vlogging','Minimalism'],
  Fitness:   ['Bodybuilding','Yoga','Home workouts','Nutrition'],
};

const STATES = {
  India: ['Delhi', 'Mumbai', 'Bangalore', 'Kolkata', 'Gujarat', 'Jaipur', 'Lucknow', 'Hyderabad', 'Pune', 'Chennai', 'Chandigarh', 'Kerala', 'Assam', 'Haryana', 'Punjab', 'Odisha', 'Goa', 'Jamnagar', 'Baroda', 'Shrirampur', 'Manipur'],
};

let currentResults = [];   
let currentCurrency = 'USD';
let chartInst = null;
let visibleCount = 6;      

let currentOfferTarget = null;
let currentOfferData = null;

let viewHistory = ['campaign'];
let historyIndex = 0;
let isNavigating = false;

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initUser();
  applyTheme(localStorage.getItem('iq_theme') || 'dark');

  const prefCur = localStorage.getItem('iq_pref_currency') || 'USD';
  currentCurrency = prefCur;
  const sel = document.getElementById('currencySelect');
  if (sel) sel.value = prefCur;
  
  const blbl = document.getElementById('budgetLabel');
  if (blbl) blbl.textContent = `Max Budget (${currentCurrency})`;

  const params = new URLSearchParams(location.search);
  if (params.get('demo') === '1') {
    setTimeout(() => {
      const cat = document.getElementById('category');
      if (cat) { cat.value = 'Tech'; onCategoryChange(); }
      setTimeout(() => {
        const sub = document.getElementById('subcategory');
        if (sub) { sub.value = 'AI/ML'; runSearch(); }
      }, 200);
    }, 600);
  }

  loadTrending();
  renderInbox();
  updateNavButtons();
});

window.addEventListener('scroll', () => {
  const btn = document.getElementById('scrollTopBtn');
  if (btn) {
    if (window.scrollY > 300) btn.style.display = 'flex';
    else btn.style.display = 'none';
  }
});

function initUser() {
  const data = localStorage.getItem('iq_user');
  if (data) {
    const u = JSON.parse(data);
    if(u.role === 'creator') {
      window.location.href = '/creator_dashboard';
      return;
    }
    const n = u.name || 'User';
    document.getElementById('userAvatar').textContent = n[0].toUpperCase();
    document.getElementById('userName').textContent = n;
  }
}

// ── View switching ────────────────────────────────────────────
function switchView(name, el, skipHistory = false) {
  document.querySelectorAll('.s-nav-item').forEach(i => i.classList.remove('active'));
  
  const navItem = el || document.querySelector(`.s-nav-item[data-view="${name}"]`);
  if (navItem) navItem.classList.add('active');

  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const targetView = document.getElementById('view-' + name);
  if (targetView) targetView.classList.add('active');

  const titles = { campaign:'New Campaign', results:'Results', trending:'Trending', analytics:'Analytics Dashboard', negotiate:'AI Negotiator', inbox:'Inbox & Offers' };
  const subs   = { campaign:'Find influencers for your brand', results:'AI-matched influencer recommendations', trending:'Trending by engagement quality', analytics:'Track campaign performance', negotiate:'Draft personalized outreach', inbox:'Manage pending collaborations' };
  
  const titleEl = document.getElementById('viewTitle');
  const subEl = document.getElementById('viewSub');
  if (titleEl) titleEl.textContent = titles[name] || name;
  if (subEl) subEl.textContent = subs[name] || '';
  
  if(name === 'analytics') renderAnalytics();
  if(name === 'inbox') renderInbox();
  if(name === 'negotiate') populateNegDropdown();

  // History logic
  if (!skipHistory && !isNavigating) {
    if (viewHistory[historyIndex] !== name) {
      viewHistory = viewHistory.slice(0, historyIndex + 1);
      viewHistory.push(name);
      historyIndex++;
    }
  }
  updateNavButtons();
}

function updateNavButtons() {
  const backBtn = document.getElementById('navBackBtn');
  const forwardBtn = document.getElementById('navForwardBtn');
  if (backBtn) backBtn.disabled = historyIndex <= 0;
  if (forwardBtn) forwardBtn.disabled = historyIndex >= viewHistory.length - 1;
}

function navHistoryBack() {
  if (historyIndex > 0) {
    isNavigating = true;
    historyIndex--;
    switchView(viewHistory[historyIndex], null, true);
    isNavigating = false;
  }
}

function navHistoryForward() {
  if (historyIndex < viewHistory.length - 1) {
    isNavigating = true;
    historyIndex++;
    switchView(viewHistory[historyIndex], null, true);
    isNavigating = false;
  }
}

function onCategoryChange() {
  const cat = document.getElementById('category').value;
  const sub = document.getElementById('subcategory');
  sub.innerHTML = '<option value="">Select sub-category…</option>';
  (SUBCATS[cat] || []).forEach(s => {
    const o = document.createElement('option');
    o.value = s; o.textContent = s; sub.appendChild(o);
  });
}

function onCountryChange() {
  const c = document.getElementById('country').value;
  const sg = document.getElementById('stateGroup');
  const s = document.getElementById('state');
  s.innerHTML = '<option value="">Any State/Region</option>';
  if (STATES[c]) {
    sg.style.display = 'flex';
    STATES[c].forEach(st => {
      const o = document.createElement('option');
      o.value = st; o.textContent = st; s.appendChild(o);
    });
  } else {
    sg.style.display = 'none';
  }
}

function onCurrencyChange() {
  const sel = document.getElementById('currencySelect');
  currentCurrency = sel.value;
  localStorage.setItem('iq_pref_currency', currentCurrency);
  
  const blbl = document.getElementById('budgetLabel');
  if (blbl) blbl.textContent = `Max Budget (${currentCurrency})`;
  
  if (currentResults.length) {
    renderCardsPaginated();
    renderChart(currentResults.slice(0, visibleCount));
  }
}

function fmtPrice(priceUSD) {
  if (!priceUSD) return null;
  const rate = RATES[currentCurrency] || 1;
  const sym  = SYMBOLS[currentCurrency] || '$';
  const val  = priceUSD * rate;
  const fmt  = currentCurrency === 'INR'
    ? val.toLocaleString('en-IN', {maximumFractionDigits:0})
    : val.toLocaleString('en-US', {maximumFractionDigits:0});
  return sym + fmt;
}

function fmtNum(n) {
  if (n >= 1e9) return (n/1e9).toFixed(1)+'B';
  if (n >= 1e6) return (n/1e6).toFixed(1)+'M';
  if (n >= 1e3) return (n/1e3).toFixed(0)+'K';
  return String(n);
}

function showSkeletons() {
  const grid = document.getElementById('cardsGrid');
  grid.innerHTML = '';
  for (let i=0; i<6; i++) {
    grid.innerHTML += `
    <div class="inf-card skeleton-card" style="animation-delay:${i*0.05}s">
      <div class="skel-head">
        <div class="skel-avatar"></div>
        <div class="skel-lines">
          <div class="skel-line w-70"></div>
          <div class="skel-line w-40"></div>
        </div>
        <div class="skel-circle"></div>
      </div>
      <div class="skel-box"></div>
      <div class="skel-box"></div>
    </div>`;
  }
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('loadMoreWrap').style.display = 'none';
  const cb = document.querySelector('.chart-block');
  if(cb) cb.style.display = 'none';
  
  document.getElementById('resultsHeading').textContent = `Searching...`;
  document.getElementById('resultsSubheading').textContent = `Analyzing influencer data...`;
}

async function runSearch() {
  const cat  = document.getElementById('category').value;
  const sub  = document.getElementById('subcategory').value;
  const plat = document.getElementById('platform').value;
  const bud  = document.getElementById('budget').value;
  const country = document.getElementById('country')?.value || '';
  const state   = document.getElementById('state')?.value || '';

  if (!cat)  { flash('Please select a category.'); return; }
  if (!sub)  { flash('Please select a sub-category.'); return; }

  const btn  = document.getElementById('findBtn');
  const txt  = document.getElementById('findBtnText');
  const ldr  = document.getElementById('findBtnLoader');
  btn.disabled = true; txt.style.display='none'; ldr.style.display='inline';

  const resNav = document.querySelector('[data-view="results"]');
  switchView('results', resNav);
  showSkeletons();

  // Convert the entered budget back to USD based on the currently selected currency
  const usdBudget = bud ? parseFloat(bud) / (RATES[currentCurrency] || 1) : null;

  try {
    const res = await fetch('/api/predict', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ 
        category:cat, subcategory:sub, platform:plat||null, 
        budget:usdBudget, country: country||null, 
        state: state||null, limit: 50
      })
    });
    const data = await res.json();
    if (data.error) { flash(data.error); return; }

    currentResults = data.results;
    window._lastResults = currentResults;
    visibleCount = 6;

    const badge = document.getElementById('resultsBadge');
    if (badge) { badge.textContent = data.total_available; badge.style.display = 'inline'; }

    const algoDisplay = data.meta.algorithm || 'TF-IDF';
    document.getElementById('resultsHeading').textContent = `Top matches for "${sub}"`;
    document.getElementById('resultsSubheading').innerHTML =
      `${data.total_available} influencer${data.total_available!==1?'s':''} · ${cat} → ${sub}${plat?' · '+plat:''}${country?' · '+country:''}${state?' · '+state:''} <span class="algo-badge">AI Model: ${algoDisplay}</span>`;

    renderCardsPaginated();
    renderChart(currentResults.slice(0, visibleCount));

  } catch(e) {
    flash('Server error — please try again.');
  }

  btn.disabled=false; txt.style.display=''; ldr.style.display='none';
}

function sortResults() {
  if (!currentResults.length) return;
  const by = document.getElementById('sortSelect').value;
  currentResults = [...currentResults].sort((a,b) => {
    if (by === 'score')      return b.suitability_score - a.suitability_score;
    if (by === 'engagement') return b.engagement_rate - a.engagement_rate;
    if (by === 'followers')  return b.followers - a.followers;
    if (by === 'price_asc')  return (a.price_usd||999999) - (b.price_usd||999999);
    if (by === 'price_desc') return (b.price_usd||0) - (a.price_usd||0);
    return 0;
  });
  visibleCount = 6;
  renderCardsPaginated();
  renderChart(currentResults.slice(0, visibleCount));
}

function renderCardsPaginated() {
  const grid = document.getElementById('cardsGrid');
  if (currentResults.length === 0) {
    grid.innerHTML = '';
    document.getElementById('emptyState').style.display = 'block';
    document.getElementById('loadMoreWrap').style.display = 'none';
    const cb = document.querySelector('.chart-block');
    if(cb) cb.style.display = 'none';
    return;
  }
  
  document.getElementById('emptyState').style.display = 'none';
  const cb = document.querySelector('.chart-block');
  if(cb) cb.style.display = 'block';
  
  const currentCount = grid.children.length;
  const toShow = currentResults.slice(0, visibleCount);
  
  if (currentCount === 0 || currentCount > toShow.length || grid.querySelector('.skeleton-card')) {
    renderCards(toShow, false, 0); 
  } else {
    const newItems = toShow.slice(currentCount);
    renderCards(newItems, true, currentCount);
  }
  
  const wrap = document.getElementById('loadMoreWrap');
  if (visibleCount < currentResults.length) {
    wrap.style.display = 'block';
    document.getElementById('loadMoreText').textContent = `Showing ${toShow.length} of ${currentResults.length}`;
  } else {
    wrap.style.display = 'none';
  }
}

function loadMoreCards() {
  visibleCount += 6;
  renderCardsPaginated();
  renderChart(currentResults.slice(0, Math.max(8, visibleCount)));
}

function renderChart(results) {
  const topN   = results.slice(0,8);
  const labels = topN.map(r => r.name.length > 14 ? r.name.slice(0,13)+'…' : r.name);
  const scores = topN.map(r => r.suitability_score);
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const gc = isDark ? 'rgba(255,255,255,.05)' : 'rgba(0,0,0,.05)';
  const tc = isDark ? '#8888aa' : '#44445e';
  const canvas = document.getElementById('scoreChart');
  if (!canvas) return;
  if (window._chartInstance) { window._chartInstance.destroy(); window._chartInstance = null; }
  window._chartInstance = new Chart(canvas.getContext('2d'), {
    type:'bar',
    data:{
      labels,
      datasets:[{
        label:'Suitability Score',
        data: scores,
        backgroundColor: scores.map((_,i) => i===0 ? 'rgba(124,92,252,.9)' : 'rgba(124,92,252,.38)'),
        borderColor:     scores.map((_,i) => i===0 ? '#7c5cfc' : 'rgba(124,92,252,.5)'),
        borderWidth:1, borderRadius:6,
      }]
    },
    options:{
      responsive:true,
      plugins:{ legend:{display:false}, tooltip:{callbacks:{label:c=>` Score: ${c.parsed.y.toFixed(1)}`}} },
      scales:{
        y:{beginAtZero:true,max:100,grid:{color:gc},ticks:{color:tc,font:{size:11}}},
        x:{grid:{display:false},ticks:{color:tc,font:{size:11}}}
      }
    }
  });
}

function renderCards(results, append=false, offset=0) {
  const grid = document.getElementById('cardsGrid');
  if (!append) grid.innerHTML = '';
  
  results.forEach((inf, idx) => {
    const globalIdx = offset + idx;
    const isTop = globalIdx === 0;
    const priceStr = fmtPrice(inf.price_usd) || 'Contact for pricing';
    const isNaPrice = !inf.price_usd;
    const engCls = inf.engagement_rate >= 5 ? 'green' : inf.engagement_rate >= 3 ? 'amber' : 'red';
    const fraudCls = inf.fraud_class === 'low' ? 'green' : inf.fraud_class === 'medium' ? 'amber' : 'red';
    const pct = Math.round(inf.suitability_score);
    const circumference = 2 * Math.PI * 26; 
    const dash = (pct / 100) * circumference;

    const reasonsHtml = (inf.reasons||[]).map(r =>
      `<div class="why-item"><span class="why-check">✔</span><span>${r}</span></div>`
    ).join('');

    const qual = inf.profile_quality || 0;
    const qColor = qual >= 80 ? 'green' : (qual >= 60 ? 'amber' : 'red');

    const card = document.createElement('div');
    card.className = 'inf-card' + (isTop ? ' top-pick' : '');
    card.style.animationDelay = `${idx * 0.055}s`;
    card.innerHTML = `
      <div class="card-head">
        <div class="card-identity">
          <div class="card-name">${inf.name}</div>
          <div class="card-badges">
            <span class="badge badge-plat">${inf.platform_icon||'📱'} ${inf.platform}</span>
            <span class="badge badge-pop">${inf.popularity_tag}</span>
            ${isTop ? '<span class="badge badge-best">⭐ Best Match</span>' : ''}
            ${inf.verified ? '<span class="badge badge-verify">✓ Verified</span>' : ''}
          </div>
          <div class="card-niche">${inf.subcategory} · ${inf.category}</div>
        </div>
        <div class="score-ring-wrap">
          <div class="score-ring" title="AI Suitability Score">
            <svg width="62" height="62" viewBox="0 0 62 62">
              <circle cx="31" cy="31" r="26" fill="none" stroke="var(--border)" stroke-width="5"/>
              <circle cx="31" cy="31" r="26" fill="none" stroke="var(--accent)" stroke-width="5"
                stroke-dasharray="${dash} ${circumference}" stroke-linecap="round"/>
            </svg>
            <div class="score-ring-inner">
              <span class="score-num">${pct}</span>
              <span class="score-tag">Score</span>
            </div>
          </div>
          <div class="cosine-tag mt-2" title="Cosine Similarity">🧠 ${inf.cosine_sim}% match</div>
        </div>
      </div>

      <div class="card-stats-grid">
        <div class="csg-item"><span class="csg-label">👥 Followers</span><span class="csg-val">${fmtNum(inf.followers)}</span></div>
        <div class="csg-item"><span class="csg-label">📊 Engagement</span><span class="csg-val ${engCls}">${inf.engagement_rate}%</span></div>
        <div class="csg-item"><span class="csg-label">❤️ Avg Likes</span><span class="csg-val">${fmtNum(inf.avg_likes)}</span></div>
        <div class="csg-item"><span class="csg-label">⚠️ Fraud Risk</span><span class="csg-val ${fraudCls}">${inf.fraud_icon} ${inf.fraud_label}</span></div>
      </div>

      <div class="card-pills">
        <span class="pill">💬 ${fmtNum(inf.avg_comments)} comments</span>
        <span class="pill">📱 ${inf.content_type}</span>
        <span class="pill">📍 ${inf.location.split(' ').slice(0,2).join(' ')}</span>
        <span class="quality-tag q-${qColor}">Quality: ${qual}/100</span>
      </div>

      <div class="reach-bar-wrap">
        <div class="reach-bar-meta"><span>Audience Reach</span><span>${fmtNum(inf.followers)}</span></div>
        <div class="reach-bar-track"><div class="reach-bar-fill" style="width:${inf.reach_pct}%"></div></div>
      </div>

      <div class="why-box">
        <div class="why-box-title">✦ Why this influencer?</div>
        ${reasonsHtml}
      </div>

      <div class="card-price-row">
        <div>
          <span class="price-label">💰 Est. Rate</span>
          <span class="price-val ${isNaPrice?'na-price':''}" data-usd="${inf.price_usd||0}">${priceStr}</span>
        </div>
        <div style="display:flex; gap:8px;">
          ${inf.platform.toLowerCase() === 'youtube' ? `<button class="btn-sm-outline" style="color:var(--text); border-color:var(--border);" onclick="syncCard(this, '${inf.name}')" title="Fetch live YouTube stats">🔄 Sync Data</button>` : ''}
          <button class="btn-sm-outline" onclick="openOfferModal('${inf.name}', ${inf.price_usd ? Math.round(inf.price_usd * (RATES[currentCurrency]||1)) : 0})">✉️ Send Offer</button>
        </div>
      </div>`;

    grid.appendChild(card);
  });
}

// ── API Sync ──────────────────────────────────────────────────
async function syncCard(btn, name) {
  const ogText = btn.innerHTML;
  btn.innerHTML = '⏳ Syncing...';
  btn.disabled = true;
  try {
    const res = await fetch('/api/sync_youtube', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name: name })
    });
    const data = await res.json();
    if(data.success) {
      const card = btn.closest('.inf-card');
      const stats = card.querySelectorAll('.csg-val');
      
      // Update DOM with live data
      if (stats.length >= 3) {
        stats[0].textContent = fmtNum(data.followers);
        stats[1].textContent = data.engagement_rate + '%';
        stats[2].textContent = fmtNum(data.avg_likes);
        
        // Update styling for engagement rate (color change)
        stats[1].className = 'csg-val ' + (data.engagement_rate >= 5 ? 'green' : data.engagement_rate >= 3 ? 'amber' : 'red');
      }
      
      btn.innerHTML = '✅ Synced Live';
      btn.style.color = 'var(--green)';
      btn.style.borderColor = 'rgba(34, 197, 94, 0.3)';
    } else {
      flash(data.error || "Failed to sync.");
      btn.innerHTML = '❌ Failed';
    }
  } catch(e) {
    flash("Server error checking API.");
    btn.innerHTML = ogText;
    btn.disabled = false;
  }
}

// ── Modals & Offers ───────────────────────────────────────────
function getOffers() {
  return JSON.parse(localStorage.getItem('iq_offers') || '[]');
}

function openOfferModal(infName, estPrice) {
  currentOfferTarget = infName;
  document.getElementById('offerTargetName').textContent = infName;
  document.getElementById('offerAmount').value = estPrice || '';
  document.getElementById('offerMessage').value = '';
  document.getElementById('offerModal').style.display = 'flex';
}

function closeOfferModal() {
  document.getElementById('offerModal').style.display = 'none';
  currentOfferTarget = null;
}

function submitOffer() {
  const msg = document.getElementById('offerMessage').value;
  const amt = document.getElementById('offerAmount').value;
  if(!msg || !amt) { flash("Please fill out both fields."); return; }
  
  const uData = JSON.parse(localStorage.getItem('iq_user') || '{"name":"Your Brand"}');
  
  const offer = {
    id: Date.now(),
    brand: uData.name,
    target: currentOfferTarget,
    message: msg,
    budget: amt,
    status: 'pending',
    date: new Date().toISOString()
  };
  
  const offers = getOffers();
  offers.push(offer);
  localStorage.setItem('iq_offers', JSON.stringify(offers));
  
  closeOfferModal();
  flash(`Offer sent to ${currentOfferTarget}!`);
  renderInbox();
}

function renderInbox() {
  const list = document.getElementById('brandInboxList');
  if(!list) return;
  const offers = getOffers();
  list.innerHTML = '';
  
  if(offers.length === 0) {
    list.innerHTML = `<div class="empty-state"><h3>No active offers</h3><p>Find an influencer and send an offer to start collaborating.</p></div>`;
    return;
  }
  
  offers.forEach(o => {
    const div = document.createElement('div');
    div.className = 'inbox-item';
    div.innerHTML = `
      <div class="inbox-item-left">
        <h4>Offer to ${o.target}</h4>
        <p><strong>Message:</strong> ${o.message}</p>
        <p><strong>Budget:</strong> $${o.budget}</p>
      </div>
      <div><span class="inbox-status status-${o.status}">${o.status}</span></div>
    `;
    list.appendChild(div);
  });
}

// ── Analytics ──────────────────────────────────────────────────
function renderAnalytics() {
  const bc = document.getElementById('budgetChart');
  const ec = document.getElementById('engagementChart');
  if(!bc || !ec) return;
  
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const gridColor = isDark ? '#222' : '#eee';
  
  if(window._bChart) window._bChart.destroy();
  window._bChart = new Chart(bc.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: ['Instagram', 'YouTube', 'TikTok', 'Remaining'],
      datasets: [{
        data: [4500, 3200, 1500, 3300],
        backgroundColor: ['#E1306C', '#FF0000', '#25F4EE', isDark?'#333344':'#ddddf0'],
        borderWidth: 0,
        hoverOffset: 12
      }]
    },
    options: { 
      responsive: true, 
      cutout: '75%',
      plugins: {
        legend: { position: 'right', labels: { color: isDark?'#f0f0ff':'#0f0f20', padding: 20, font: {family: 'Plus Jakarta Sans', size: 13, weight: 600} } },
        tooltip: {
          backgroundColor: isDark ? 'rgba(20,20,30,0.9)' : 'rgba(255,255,255,0.9)',
          titleColor: isDark ? '#fff' : '#000',
          bodyColor: isDark ? '#ccc' : '#444',
          padding: 12,
          cornerRadius: 8,
          borderColor: isDark ? 'rgba(124,92,252,0.3)' : 'rgba(124,92,252,0.1)',
          borderWidth: 1
        }
      } 
    }
  });

  if(window._eChart) window._eChart.destroy();
  window._eChart = new Chart(ec.getContext('2d'), {
    type: 'bar',
    data: {
      labels: ['Micro', 'Mid-tier', 'Macro', 'Mega'],
      datasets: [{
        label: 'Avg Engagement Rate %',
        data: [7.2, 5.1, 3.4, 2.1],
        backgroundColor: '#7c5cfc',
        borderRadius: 4
      }]
    },
    options: { responsive: true, scales: { y: { grid: { color: gridColor } }, x: { grid: { display: false } } } }
  });
}

// ── AI Negotiator ──────────────────────────────────────────────
function onNegTargetChange() {
  const idx = document.getElementById('negTarget').value;
  if(idx !== "") {
    const inf = currentResults[idx];
    const rate = RATES[currentCurrency] || 1;
    const localPrice = inf.price_usd ? Math.round(inf.price_usd * rate) : Math.round(500 * rate);
    document.getElementById('negBudget').value = localPrice;
  }
}

function populateNegDropdown() {
  const sel = document.getElementById('negTarget');
  if(!sel) return;
  sel.innerHTML = '<option value="">Select an influencer...</option>';
  if(currentResults.length > 0) {
    currentResults.slice(0, 20).forEach((inf, idx) => {
      sel.innerHTML += `<option value="${idx}">${inf.name} (${inf.platform})</option>`;
    });
  } else {
    sel.innerHTML = '<option value="">Search for influencers first...</option>';
  }
}

async function generateScript() {
  const idx = document.getElementById('negTarget').value;
  if(idx === "") { flash("Please select an influencer."); return; }
  
  const inf = currentResults[idx];
  const goal = document.getElementById('negGoal').value || 'Brand Awareness';
  const budgetLocal = document.getElementById('negBudget').value || 500;
  
  const sym = SYMBOLS[currentCurrency] || '$';
  let formattedBudget = sym + parseFloat(budgetLocal).toLocaleString(currentCurrency==='INR'?'en-IN':'en-US');
  
  try {
    const res = await fetch('/api/negotiate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ influencer: inf, goal: goal, budget: formattedBudget })
    });
    const data = await res.json();
    document.getElementById('scriptOutput').style.display = 'block';
    document.getElementById('generatedText').value = data.script;
    currentOfferData = { name: inf.name, budget: budgetLocal };
  } catch(e) {
    flash("Error generating script.");
  }
}

function copyScript() {
  const txt = document.getElementById('generatedText');
  txt.select();
  document.execCommand('copy');
  flash("Script copied to clipboard!");
}

function sendScriptAsOffer() {
  const txt = document.getElementById('generatedText').value;
  if(!currentOfferData) return;
  currentOfferTarget = currentOfferData.name;
  
  document.getElementById('offerTargetName').textContent = currentOfferTarget;
  document.getElementById('offerAmount').value = currentOfferData.budget;
  document.getElementById('offerMessage').value = "Outreach Pitch:\n\n" + txt;
  
  document.getElementById('offerModal').style.display = 'flex';
}

// ── Trending ──────────────────────────────────────────────────
async function loadTrending() {
  try {
    const res = await fetch('/api/trending?limit=9');
    const data = await res.json();
    const grid = document.getElementById('trendingGrid');
    if (!grid) return;
    grid.innerHTML = '';
    (data.trending || []).forEach((t, i) => {
      const card = document.createElement('div');
      card.className = 'trend-card';
      card.style.animationDelay = `${i * 0.07}s`;
      card.innerHTML = `
        <div class="trend-rank">${String(i+1).padStart(2,'0')}</div>
        <div class="trend-name">${t.name}${t.verified?' ✓':''}</div>
        <div class="trend-cat">${t.subcategory} · ${t.platform}</div>
        <div class="trend-stat">
          <span>👥 ${fmtNum(t.followers)}</span>
          <span class="trend-fire">🔥 ${t.engagement_rate}%</span>
        </div>`;
      grid.appendChild(card);
    });
  } catch(e) { console.warn('Trending load failed', e); }
}

function flash(msg) {
  let el = document.getElementById('flashMsg');
  if (!el) {
    el = document.createElement('div');
    el.id = 'flashMsg';
    el.style.cssText = 'position:fixed;top:80px;left:50%;transform:translateX(-50%);background:rgba(239,68,68,.95);color:#fff;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;z-index:999;box-shadow:0 4px 20px rgba(0,0,0,.3)';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 3000);
}
