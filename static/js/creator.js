/* InfluenceIQ v2 — Creator Dashboard Logic */

document.addEventListener('DOMContentLoaded', () => {
  const data = localStorage.getItem('iq_user');
  if (data) {
    const u = JSON.parse(data);
    if(u.role !== 'creator') {
      window.location.href = '/dashboard';
      return;
    }
    const n = u.name || 'Creator';
    document.getElementById('creatorAvatar').textContent = n[0].toUpperCase();
    document.getElementById('creatorName').textContent = n;
    document.getElementById('welcomeName').textContent = n;
  } else {
    window.location.href = '/login';
  }
  
  renderOffers();
  renderGrowthChart();
});

function switchView(name, el) {
  document.querySelectorAll('.s-nav-item').forEach(i => i.classList.remove('active'));
  el.classList.add('active');
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById('view-' + name).classList.add('active');
  
  if (name === 'overview') {
    document.getElementById('viewTitle').textContent = 'Overview';
    document.getElementById('viewSub').textContent = 'Your profile metrics';
  } else {
    document.getElementById('viewTitle').textContent = 'My Offers';
    document.getElementById('viewSub').textContent = 'Inbound brand partnerships';
  }
}

function getOffers() {
  return JSON.parse(localStorage.getItem('iq_offers') || '[]');
}

function saveOffers(offers) {
  localStorage.setItem('iq_offers', JSON.stringify(offers));
}

function renderOffers() {
  const list = document.getElementById('creatorOffersList');
  if(!list) return;
  const offers = getOffers();
  list.innerHTML = '';
  
  let pendingCount = 0;
  
  if (offers.length === 0) {
    list.innerHTML = `<div class="empty-state"><h3>No offers yet</h3><p>Your inbox is clean! Brands will send you offers here.</p></div>`;
  } else {
    // Reverse so newest is first
    [...offers].reverse().forEach((o, revIdx) => {
      const idx = offers.length - 1 - revIdx;
      if (o.status === 'pending') pendingCount++;
      const div = document.createElement('div');
      div.className = 'inbox-item';
      
      let actionsHtml = '';
      if (o.status === 'pending') {
        actionsHtml = `
          <div style="display:flex;gap:8px;margin-top:10px;">
            <button class="btn-sm-outline" style="color:var(--green);border-color:rgba(34,197,94,0.3);" onclick="updateOffer(${idx}, 'accepted')">Accept Offer</button>
            <button class="btn-sm-outline" style="color:var(--red);border-color:rgba(239,68,68,0.3);" onclick="updateOffer(${idx}, 'declined')">Decline</button>
          </div>
        `;
      }
      
      div.innerHTML = `
        <div class="inbox-item-left">
          <h4>Offer from ${o.brand}</h4>
          <p style="margin-top:4px; margin-bottom:8px;"><strong>Deliverables:</strong> ${o.message}</p>
          <p><strong>Budget:</strong> $${o.budget}</p>
        </div>
        <div style="display:flex; flex-direction:column; align-items:flex-end;">
          <span class="inbox-status status-${o.status}">${o.status}</span>
          ${actionsHtml}
        </div>
      `;
      list.appendChild(div);
    });
  }
  
  const badge = document.getElementById('creatorInboxBadge');
  if (pendingCount > 0) {
    badge.textContent = pendingCount;
    badge.style.display = 'inline';
  } else {
    badge.style.display = 'none';
  }
}

function updateOffer(idx, status) {
  let offers = getOffers();
  offers[idx].status = status;
  saveOffers(offers);
  renderOffers();
}

function renderGrowthChart() {
  const canvas = document.getElementById('growthChart');
  if (!canvas) return;
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [{
        label: 'Followers',
        data: [1.02, 1.05, 1.08, 1.12, 1.18, 1.2],
        borderColor: '#7c5cfc',
        backgroundColor: isDark ? 'rgba(124,92,252,0.1)' : 'rgba(124,92,252,0.2)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { grid: { color: isDark ? '#222' : '#eee' }, ticks: { callback: v => v + 'M' } },
        x: { grid: { display: false } }
      }
    }
  });
}
