/* ── Premium Dashboard Scripts ── */

/* ── Slider helpers ─────────────────────────────────────── */
function updateSlider(inputId, valId, fillId, min, max, unit) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const val = parseFloat(input.value);
  const valDisplay = document.getElementById(valId);
  if (valDisplay) valDisplay.textContent = val + unit;
  
  const fill = document.getElementById(fillId);
  if (fill) {
    const pct = ((val - min) / (max - min)) * 100;
    fill.style.width = pct + '%';
  }
}

/* ── Guidelines map ─────────────────────────────────────── */
const guidelines = {
  'Urea': 'Apply in split doses — 50% at sowing, 50% at tillering',
  'DAP': 'Apply as basal during soil preparation before sowing',
  'NPK 15-15-15': 'Broadcast evenly and incorporate before first irrigation',
  'SOP': 'Apply as basal for potassium-deficient soils',
  'SSP': 'Apply in furrows at time of sowing for best P uptake',
};

/* ── Submit ──────────────────────────────────────────────── */
async function submitForm() {
  const crop = document.getElementById('crop').value;
  const N = parseFloat(document.getElementById('nitrogen').value);
  const P = parseFloat(document.getElementById('phosphorus').value);
  const K = parseFloat(document.getElementById('potassium').value);
  const ph = parseFloat(document.getElementById('ph').value);
  const area = parseFloat(document.getElementById('area').value) || 1;

  if (!crop) { showToast('Please select a crop type', true); return; }

  const btn = document.getElementById('submit-btn');
  btn.classList.add('loading');

  const area_ha = area * 0.405;

  try {
    const response = await fetch('/api/v1/predict/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ crop, nitrogen: N, phosphorus: P, potassium: K, ph, area_ha })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    btn.classList.remove('loading');
    showResult(result, crop, N, P, K, ph, area);
    addHistory(crop, N, P, K, ph, result);
    showToast('✅ Recommendation ready!');
  } catch (err) {
    btn.classList.remove('loading');
    showToast('Error getting recommendation', true);
    console.error(err);
  }
}

function showResult(r, crop, N, P, K, ph, area) {
  const placeholder = document.getElementById('placeholder');
  if (placeholder) placeholder.style.display = 'none';
  
  const rc = document.getElementById('result-content');
  if (rc) rc.classList.add('visible');

  const nameEl = document.getElementById('rec-name');
  if (nameEl) nameEl.textContent = r.fertilizer;
  
  const guideEl = document.getElementById('rec-guideline');
  if (guideEl) guideEl.textContent = guidelines[r.fertilizer] || '';

  const area_ha = area * 0.405;
  const totalQty = (r.recommended_quantity_kg_ha * area_ha).toFixed(1);
  const qtyEl = document.getElementById('rec-qty');
  if (qtyEl) qtyEl.textContent = `${totalQty} kg`;

  const confEl = document.getElementById('conf-pct');
  if (confEl) confEl.textContent = r.confidence + '%';
  
  const confBar = document.getElementById('conf-bar');
  if (confBar) {
    setTimeout(() => {
      confBar.style.width = r.confidence + '%';
    }, 100);
  }

  // Deficits
  const maxDef = 100;
  ['N', 'P', 'K'].forEach(key => {
    const val = r.deficits[key] || 0;
    const defEl = document.getElementById(key.toLowerCase() + '-def');
    if (defEl) defEl.textContent = val + ' kg/ha needed';
    
    const barEl = document.getElementById(key.toLowerCase() + '-bar');
    if (barEl) {
      setTimeout(() => {
        barEl.style.width = Math.min(100, (val / maxDef) * 100) + '%';
      }, 200);
    }
  });

  // All probs
  const grid = document.getElementById('probs-grid');
  if (grid) {
    grid.innerHTML = '';
    const sorted = Object.entries(r.all_probs).sort((a, b) => b[1] - a[1]);
    sorted.forEach(([name, pct]) => {
      const div = document.createElement('div');
      div.className = 'prob-row' + (name === r.fertilizer ? ' top' : '');
      div.innerHTML = `<span class="prob-name">${name}</span><span class="prob-pct">${pct}%</span>`;
      grid.appendChild(div);
    });
  }
}

function addHistory(crop, N, P, K, ph, result) {
  const tbody = document.getElementById('history-body');
  if (!tbody) return;
  
  const tr = document.createElement('tr');
  const isGreen = result.confidence > 85;
  tr.innerHTML = `
    <td>${crop}</td>
    <td>${N}/${P}/${K}</td>
    <td>${ph}</td>
    <td><span class="badge ${isGreen ? 'badge-green' : 'badge-amber'}">${result.fertilizer}</span></td>
    <td>${result.confidence}%</td>
  `;
  tbody.insertBefore(tr, tbody.firstChild);
  if (tbody.children.length > 5) tbody.removeChild(tbody.lastChild);
}

/* ── Toast ───────────────────────────────────────────────── */
function showToast(msg, isError = false) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className = 'toast show' + (isError ? ' error' : '');
  setTimeout(() => t.className = 'toast', 3000);
}
