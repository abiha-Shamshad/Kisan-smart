/* ── Kisan Smart: Advanced Multi-Tool Controller ── */

const API_PREDICT = '/predict';

// Initialize hub summaries on load
document.addEventListener('DOMContentLoaded', () => {
  // Sync with user data if available
  const user = api.getUser();
  if (user) console.log("Welcome back,", user.username);
  
  // Set default date for schedule
  const dateInput = document.getElementById('sched-sow-date');
  if (dateInput) dateInput.value = new Date().toISOString().split('T')[0];
});

/* ── Tab 1: NPK Calculator ────────────────────────────────── */

async function runCalculation() {
    const data = {
        crop_type: document.getElementById('calc-crop').value,
        field_area: parseFloat(document.getElementById('calc-area').value) || 1,
        nitrogen: parseFloat(document.getElementById('calc-n').value) || 20,
        phosphorus: parseFloat(document.getElementById('calc-p').value) || 8,
        potassium: parseFloat(document.getElementById('calc-k').value) || 120,
        ph: parseFloat(document.getElementById('calc-ph').value) || 7.2,
        soil_texture: document.getElementById('calc-texture').value,
        prev_crop: document.getElementById('calc-prev-crop').value,
        organic_matter: document.getElementById('calc-org-matter').value
    };

    const btn = event.currentTarget;
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin me-2"></i> Analyzing Soil...';
    btn.disabled = true;

    try {
        const response = await api.request(`${API_PREDICT}/calculate-npk`, 'POST', data);
        if (response.success) {
            renderCalcResult(response.data);
            showToast('✅ Recommendation generated!');
            
            // Auto-fill budget and schedule inputs for seamless flow
            document.getElementById('sched-n').value = response.data.nutrients.per_acre.N;
            document.getElementById('sched-p').value = response.data.nutrients.per_acre.P;
        }
    } catch (err) {
        showToast(err.message || 'Calculation failed', true);
    } finally {
        btn.innerHTML = '<i class="fas fa-magic me-2"></i> Generate Smart Recommendation';
        btn.disabled = false;
    }
}

function renderCalcResult(r) {
    document.getElementById('calc-result-placeholder').style.display = 'none';
    const view = document.getElementById('calc-result-view');
    view.style.display = 'block';

    view.innerHTML = `
        <div class="card-premium reveal secondary shadow-lg border-0" style="background: white;">
            <div class="card-title-premium text-green d-flex justify-content-between">
                <span><i class="fas fa-check-circle"></i> Optimal Plan</span>
                <span class="badge bg-light text-green small border">${r.crop}</span>
            </div>
            
            <p class="small text-gray-4 mb-3">Total recommended fertilizer for <strong>${r.acres} Acres</strong>:</p>
            
            <div class="npk-row-compact">
                <div class="npk-box-compact n">
                    <div class="label">Urea</div>
                    <div class="value">${r.fertilizers.urea}</div>
                    <div class="unit">kg</div>
                </div>
                <div class="npk-box-compact p">
                    <div class="label">DAP</div>
                    <div class="value">${r.fertilizers.dap}</div>
                    <div class="unit">kg</div>
                </div>
                <div class="npk-box-compact k">
                    <div class="label">SOP</div>
                    <div class="value">${r.fertilizers.sop}</div>
                    <div class="unit">kg</div>
                </div>
            </div>

            <div class="alert-premium ${r.ph_status.type}">
                <i class="fas fa-info-circle mt-1"></i>
                <div>
                   <strong>pH Advice:</strong> ${r.ph_status.message}
                </div>
            </div>

            ${r.texture_warning ? `
                <div class="alert-premium info">
                    <i class="fas fa-exclamation-triangle mt-1"></i>
                    <div>${r.texture_warning}</div>
                </div>
            ` : ''}

            <div class="mt-4 pt-3 border-top d-flex gap-2">
                <button class="btn btn-primary flex-grow-1 py-2 btn-premium" onclick="switchTab('schedule')">
                    <i class="fas fa-calendar-alt me-2"></i> View split timing
                </button>
                <a href="https://wa.me/?text=My%20Kisan%20Smart%20Plan:%20Urea:${r.fertilizers.urea}kg,%20DAP:${r.fertilizers.dap}kg%20for%20${r.crop}" 
                   class="btn-wa" target="_blank">
                    <i class="fab fa-whatsapp"></i> Share
                </a>
            </div>
        </div>
    `;
}

/* ── Tab 2: Budget Optimizer ──────────────────────────────── */

async function runBudgetOptimization() {
    const data = {
        budget: parseFloat(document.getElementById('budget-amount').value),
        crop_price_per_40kg: parseFloat(document.getElementById('budget-crop-price').value),
        market_prices: {
            urea: parseFloat(document.getElementById('price-urea').value),
            dap: parseFloat(document.getElementById('price-dap').value),
            sop: parseFloat(document.getElementById('price-sop').value),
            can: 2800, ssp: 2200, np: 5500 // static defaults for now
        },
        requirements: {
            N: parseFloat(document.getElementById('sched-n').value) || 60,
            P: parseFloat(document.getElementById('sched-p').value) || 30,
            K: parseFloat(document.getElementById('sched-k')?.value || 20)
        }
    };

    try {
        const response = await api.request(`${API_PREDICT}/budget-optimize`, 'POST', data);
        if (response.success) {
            renderBudgetResult(response.data);
            showToast('💰 Budget optimization complete');
        }
    } catch (err) {
        showToast('Error optimizing budget', true);
    }
}

function renderBudgetResult(r) {
    const view = document.getElementById('budget-result-view');
    view.style.display = 'block';
    
    view.innerHTML = `
        <div class="row g-3 reveal mt-2">
            <div class="col-md-4">
                <div class="budget-metric card-premium">
                    <div class="small fw-600 text-gray-4">Budget Fill</div>
                    <div class="metric-val text-green">${r.ratio}%</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="budget-metric card-premium">
                    <div class="small fw-600 text-gray-4">Est. Profit</div>
                    <div class="metric-val text-blue">Rs. ${r.financials.profit.toLocaleString()}</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="budget-metric card-premium">
                    <div class="small fw-600 text-gray-4">Overall ROI</div>
                    <div class="metric-val text-amber">${r.financials.roi}%</div>
                </div>
            </div>
        </div>
        
        <div class="card-premium mt-3 border-green-light">
            <div class="small fw-bold text-gray-5 mb-3">CHEAPEST FERTILIZER ALLOCATION</div>
            ${r.plan.fertilizers.map(f => `
                <div class="d-flex justify-content-between border-bottom py-2">
                    <span>${f.name}</span>
                    <span class="fw-bold">${f.qty} kg <small class="text-muted">(Rs. ${f.cost})</small></span>
                </div>
            `).join('')}
        </div>
    `;
}

/* ── Tab 3: Schedule ───────────────────────────────────────── */

async function runScheduleGeneration() {
    const data = {
        crop_type: document.getElementById('calc-crop').value,
        total_n: parseFloat(document.getElementById('sched-n').value),
        total_p: parseFloat(document.getElementById('sched-p').value),
        total_k: parseFloat(document.getElementById('sched-k')?.value || 20),
        sow_date: document.getElementById('sched-sow-date').value
    };

    try {
        const response = await api.request(`${API_PREDICT}/generate-schedule`, 'POST', data);
        if (response.success) {
            renderScheduleResult(response.data);
            showToast('📅 Schedule generated');
        }
    } catch (err) {
        showToast('Error generating schedule', true);
    }
}

function renderScheduleResult(data) {
    const view = document.getElementById('schedule-result-view');
    view.style.display = 'block';
    
    view.innerHTML = `
        <div class="card-premium p-0 overflow-hidden reveal mt-3">
            <div class="schedule-table-wrapper">
                <table class="schedule-table">
                    <thead>
                        <tr>
                            <th>Growth Stage</th>
                            <th>Target Date</th>
                            <th class="text-center">Dose (N/P/K)</th>
                            <th>Best Fertilizer Combination</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(s => `
                            <tr>
                                <td><div class="fw-600 text-green-mid">${s.stage}</div></td>
                                <td><div class="small text-gray-5">${s.date}</div></td>
                                <td class="text-center">
                                    <span class="badge bg-light text-blue border small">${s.N}</span>
                                    <span class="badge bg-light text-amber border small">${s.P}</span>
                                    <span class="badge bg-light text-green border small">${s.K}</span>
                                </td>
                                <td><div class="small fw-500">${s.suggestion}</div></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="p-3 bg-light border-top text-center text-gray-4 small italic">
                <i class="fas fa-info-circle me-1"></i> Timings are based on average crop maturity cycles and may vary by weather.
            </div>
        </div>
    `;
}

/* ── Tab 4: AI Scan ────────────────────────────────────────── */

function previewScanImage(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(ev) {
            const preview = document.getElementById('image-preview');
            preview.src = ev.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
}

async function runAIScan() {
    const input = document.getElementById('ai-image-input');
    if (!input.files || input.files.length === 0) {
        showToast('Please select or take a photo first', true);
        return;
    }

    const btn = document.getElementById('scan-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin me-2"></i> Plant Vision AI analyzing...';
    btn.disabled = true;

    const file = input.files[0];
    const reader = new FileReader();
    
    reader.onload = async function() {
        const base64Image = reader.result;
        try {
            const response = await api.request(`${API_PREDICT}/ai-scan`, 'POST', {
                image: base64Image,
                crop_type: document.getElementById('calc-crop').value
            });
            
            if (response.success) {
                renderScanResult(response.data);
                showToast('✅ Analysis complete');
            }
        } catch (err) {
            showToast('AI Analysis failed', true);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    };
    reader.readAsDataURL(file);
}

function renderScanResult(r) {
    const view = document.getElementById('scan-result-view');
    view.style.display = 'block';
    
    const isMock = r.is_mock;
    const colorClass = r.deficiency.includes('Deficiency') ? 'danger' : 'success';
    const icon = r.deficiency.includes('Deficiency') ? 'fa-exclamation-triangle' : 'fa-check-circle';

    view.innerHTML = `
        <div class="card-premium mt-3 border-${colorClass} reveal shadow-sm" style="background: white;">
            <div class="card-title-premium text-${colorClass}">
                <i class="fas ${icon}"></i> ${r.deficiency}
            </div>
            
            <div class="row align-items-center mb-3">
                <div class="col-auto">
                    <div style="font-size: 3rem;">${r.deficiency.includes('Nitrogen') ? '🍂' : '🌿'}</div>
                </div>
                <div class="col">
                    <div class="fw-bold mb-1">${r.deficiency}</div>
                    <div class="small text-muted">Identification Confidence: ${Math.round(r.confidence * 100)}%</div>
                </div>
            </div>

            <p class="text-gray-5 small mb-3">${r.description}</p>
            
            <div class="alert-premium success py-3">
                <div class="d-flex gap-2">
                    <i class="fas fa-hand-holding-seedling mt-1"></i>
                    <div>
                        <strong>Recommended Solution:</strong><br>
                        ${r.solution}
                    </div>
                </div>
            </div>
            
            ${isMock ? `<div class="mt-2 text-center"><small class="text-muted italic text-xs">Note: AI Model is currently in simulation mode.</small></div>` : ''}
        </div>
    `;
}

/* ── Tab 5: History (Server-Side) ─────────────────────────── */

async function loadServerHistory() {
    const loading = document.getElementById('history-loading');
    const view = document.getElementById('history-view');
    
    loading.style.display = 'block';
    view.style.display = 'none';

    try {
        const response = await api.request('/history', 'GET');
        if (response.success) {
            renderHistoryRecords(response.data);
        }
    } catch (err) {
        console.error(err);
        view.innerHTML = '<div class="text-center py-5 text-gray-4">History unavailable or requires login.</div>';
        view.style.display = 'block';
    } finally {
        loading.style.display = 'none';
    }
}

function renderHistoryRecords(data) {
    const view = document.getElementById('history-view');
    view.style.display = 'block';
    
    if (!data || data.length === 0) {
        view.innerHTML = '<div class="text-center py-5 text-gray-4">No past records found. Start with a calculation!</div>';
        return;
    }

    view.innerHTML = `
        <div class="card-premium reveal p-0 overflow-hidden">
            <table class="history-table w-100 mb-0">
                <thead class="bg-light">
                    <tr>
                        <th class="p-3">Date</th>
                        <th class="p-3">Crop</th>
                        <th class="p-3">Recommendation</th>
                        <th class="p-3">Method</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.slice(0, 10).map(h => `
                        <tr class="border-bottom">
                            <td class="p-3 small text-muted">${new Date(h.created_at).toLocaleDateString()}</td>
                            <td class="p-3 fw-600">${h.crop_type}</td>
                            <td class="p-3 small">${h.fertilizer_type}</td>
                            <td class="p-3"><span class="badge bg-light text-primary border">${h.confidence_level}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

/* ── UI Helpers ───────────────────────────────────────────── */

function showToast(msg, isError = false) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.className = 'toast show' + (isError ? ' error' : '');
    setTimeout(() => t.className = 'toast', 3000);
}
