/* ── Pest Control Center JS ── */

let currentData = null;
let selectedPest = null;

const SEV_ORDER = ['Low', 'Medium', 'High', 'Critical'];
const SEV_COLOR = { Critical: '#DC2626', High: '#D97706', Medium: '#EA580C', Low: '#059669' };
const SEV_BG    = { Critical: 'bg-red-50 border-red-200', High: 'bg-amber-50 border-amber-200', Medium: 'bg-orange-50 border-orange-200', Low: 'bg-green-50 border-green-200' };
const SEV_BADGE = { Critical: 'sev-badge-critical', High: 'sev-badge-high', Medium: 'sev-badge-medium', Low: 'sev-badge-low' };
const BAR_CLASS = { Critical: 'bar-fill-critical', High: 'bar-fill-high', Medium: 'bar-fill-medium', Low: 'bar-fill-low' };

async function loadPestData() {
    const crop = document.getElementById('crop-select')?.value || 'Wheat';
    const lat = 32.57, lon = 74.08;

    setGrid('<div class="sm:col-span-2 py-10 text-center text-gray-400"><i class="fas fa-spinner fa-spin text-3xl block mb-3 text-green-400"></i><p class="text-sm">Analyzing weather patterns...</p></div>');
    document.getElementById('assessed-label').textContent = 'Loading...';

    try {
        const [data, alertsData] = await Promise.all([
            api.request(`/pest/assess?lat=${lat}&lon=${lon}&crop=${crop}`),
            api.request(`/pest/district-alerts?lat=${lat}&lon=${lon}&crop=${crop}`)
        ]);
        currentData = data;
        renderStats(data);
        renderPestGrid(data);
        renderDistrictBanners(alertsData.alerts);
        document.getElementById('assessed-label').textContent = `${data.crop} · ${new Date().toLocaleTimeString('en-PK', { hour: '2-digit', minute: '2-digit' })}`;
    } catch (err) {
        setGrid(`<div class="sm:col-span-2 py-10 text-center text-red-400"><i class="fas fa-exclamation-triangle text-3xl block mb-3"></i><p class="text-sm">${err.message}</p></div>`);
        showToast(err.message, true);
    }
}

function renderStats(data) {
    const risks = data.risks || [];
    document.getElementById('stat-total').textContent = risks.length;
    document.getElementById('stat-critical').textContent = risks.filter(r => r.severity === 'Critical' || r.severity === 'High').length;
    const avg = risks.length ? Math.round(risks.reduce((s, r) => s + r.score, 0) / risks.length) : 0;
    document.getElementById('stat-avg').textContent = avg;
}

function renderPestGrid(data) {
    const risks = data.risks || [];
    if (!risks.length) {
        setGrid('<div class="sm:col-span-2 py-10 text-center text-gray-400 text-sm">✅ No significant pest risks detected for your crop.</div>');
        return;
    }

    const sorted = [...risks].sort((a, b) => b.score - a.score);
    document.getElementById('pest-grid').innerHTML = sorted.map(r => `
        <div class="pest-card bg-white border ${SEV_BG[r.severity]} border rounded-2xl p-5 shadow-sm"
             onclick="selectPest('${r.pest.replace(/'/g, "\\'")}')">
            <div class="flex items-start justify-between mb-3">
                <div>
                    <div class="font-syne font-bold text-gray-900 text-base">${r.pest}</div>
                    <div class="text-gray-400 text-xs mt-0.5">${data.crop}</div>
                </div>
                <span class="text-xs font-bold px-2 py-0.5 rounded-full ${SEV_BADGE[r.severity]}">${r.severity}</span>
            </div>
            <div class="mb-3">
                <div class="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Risk Score</span>
                    <span class="font-bold" style="color:${SEV_COLOR[r.severity]}">${r.score}/100</span>
                </div>
                <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div class="h-2 rounded-full ${BAR_CLASS[r.severity]} transition-all duration-700" 
                         style="width:0%" data-w="${r.score}%"></div>
                </div>
            </div>
            <div class="text-xs text-gray-400 flex items-center gap-1">
                <i class="fas fa-chevron-right" style="color:${SEV_COLOR[r.severity]}; font-size:.6rem;"></i>
                Click for treatment details
            </div>
        </div>
    `).join('');

    setTimeout(() => document.querySelectorAll('[data-w]').forEach(el => el.style.width = el.dataset.w), 100);
}

function selectPest(name) {
    const risk = currentData?.risks.find(r => r.pest === name);
    if (!risk) return;

    // Toggle
    if (selectedPest === name) {
        selectedPest = null;
        document.getElementById('detail-panel').innerHTML = `<div class="p-8 text-center text-gray-400"><i class="fas fa-hand-pointer text-3xl mb-3 block" style="color:#2D6A4F"></i><p class="text-sm">Click a pest card to see details.</p></div>`;
        document.querySelectorAll('.pest-card').forEach(c => c.classList.remove('selected'));
        return;
    }
    selectedPest = name;
    document.querySelectorAll('.pest-card').forEach(c => c.classList.remove('selected'));
    event.currentTarget.classList.add('selected');

    const icons = { Critical: '🚨', High: '⚠️', Medium: '🔶', Low: '✅' };
    const triggers = risk.triggered_by?.length
        ? risk.triggered_by.map(t => `<li class="flex items-start gap-2 text-sm text-gray-600"><span class="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0" style="background:${SEV_COLOR[risk.severity]}"></span>${t}</li>`).join('')
        : '<li class="text-sm text-gray-400">No specific weather triggers identified.</li>';

    document.getElementById('detail-panel').innerHTML = `
        <div class="p-5 border-b border-gray-100 flex items-center gap-3" style="background:${SEV_BG[risk.severity].split(' ')[0].replace('bg-','').includes('red') ? '#FEF2F2' : SEV_BG[risk.severity].split(' ')[0] === 'bg-amber-50' ? '#FFFBEB' : '#FFF7ED'}">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl">
                ${icons[risk.severity] || '🌿'}
            </div>
            <div>
                <div class="font-syne font-bold text-lg text-gray-900">${risk.pest}</div>
                <div class="text-xs text-gray-500">${risk.severity} Risk · Score ${risk.score}/100</div>
            </div>
        </div>
        <div class="p-5 space-y-4">
            <div class="bg-gray-50 rounded-xl p-4">
                <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">Recommended Action</div>
                <div class="text-sm text-gray-800 font-medium">${risk.treatment}</div>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
                <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">Chemical Control</div>
                <div class="text-sm text-gray-800 font-medium">${risk.pesticide}</div>
            </div>
            <div>
                <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Weather Triggers</div>
                <ul class="space-y-1">${triggers}</ul>
            </div>
        </div>
    `;
}

function renderDistrictBanners(alerts) {
    const container = document.getElementById('district-banners');
    const confirmed = (alerts || []).filter(a => a.confirmed || a.max_severity === 'Critical');
    if (!confirmed.length) { container.innerHTML = ''; return; }

    container.innerHTML = confirmed.map(a => `
        <div class="flex items-start gap-3 p-4 rounded-2xl border ${a.max_severity === 'Critical' ? 'bg-red-50 border-red-200' : 'bg-amber-50 border-amber-200'}">
            <span class="text-xl flex-shrink-0">${a.max_severity === 'Critical' ? '🚨' : '⚠️'}</span>
            <div>
                <div class="font-bold text-sm text-gray-900">${a.max_severity} Alert: ${a.pest} reported in your district</div>
                <div class="text-xs text-gray-500 mt-0.5">Confirmed by ${a.report_count} nearby farmers. Inspect your fields immediately.</div>
            </div>
        </div>
    `).join('');
}

async function submitReport() {
    const crop     = document.getElementById('r-crop').value;
    const pest     = document.getElementById('r-pest').value;
    const severity = document.getElementById('r-severity').value;
    const btn      = document.getElementById('btn-submit');

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Submitting...';

    try {
        await api.request('/pest/report', {
            method: 'POST',
            body: JSON.stringify({ crop, pest_name: pest, severity, lat: 32.57, lon: 74.08 })
        });
        showToast('✅ Sighting reported! Thank you for helping the community.');
        document.getElementById('r-location').value = '';
    } catch (err) {
        showToast(err.message, true);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Submit Report — رپورٹ کریں';
    }
}

function setGrid(html) {
    document.getElementById('pest-grid').innerHTML = html;
}

function showToast(msg, isErr = false) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.className = `fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl text-white text-sm font-semibold shadow-xl transition-all ${isErr ? 'bg-red-500' : 'bg-green-600'}`;
    setTimeout(() => t.className = 'fixed bottom-6 right-6 z-50 hidden', 4000);
}

document.addEventListener('DOMContentLoaded', loadPestData);
