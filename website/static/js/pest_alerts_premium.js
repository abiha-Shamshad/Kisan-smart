/* ── Premium Pest Alerts Scripts ── */

let currentData = null;
let selectedPestName = null;

// Helper for classes
const sevClass = s => s === 'Critical' ? 'critical' : s === 'High' ? 'high' : s === 'Medium' ? 'medium' : 'low';
const fillClass = s => 'fill-' + sevClass(s);
const bannerClass = s => 'ab-' + sevClass(s);

async function initPestAlerts() {
    // api is a global instance from api.js
    if (!api.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }

    // Default to Gujrat, Punjab if no location set
    const lat = 32.57;
    const lon = 74.08;
    const crop = 'Wheat';

    try {
        // Use api client
        const data = await api.request(`/pest/assess?lat=${lat}&lon=${lon}&crop=${crop}`);
        currentData = data;
        renderPests(data);

        // Fetch district alerts
        const alerts = await api.request(`/pest/district-alerts?lat=${lat}&lon=${lon}&crop=${crop}`);
        renderDistrictBanners(alerts.alerts);

    } catch (err) {
        showPestToast(err.message, true);
        const grid = document.getElementById('score-grid');
        if (grid) grid.innerHTML = `<p style="padding:2rem;color:var(--red);text-align:center;grid-column:1/-1;">Error loading data. Please try again.</p>`;
    }
}

function renderPests(data) {
    const cropLabel = document.getElementById('crop-label');
    if (cropLabel) cropLabel.textContent = `${data.crop} — Region: ${data.location.lat}, ${data.location.lon}`;

    const grid = document.getElementById('score-grid');
    if (!grid) return;

    if (!data.risks || data.risks.length === 0) {
        grid.innerHTML = `<p style="padding:2rem;color:var(--muted);text-align:center;grid-column:1/-1;">No risks detected for your crop currently.</p>`;
        return;
    }

    grid.innerHTML = data.risks.map(r => `
        <div class="score-card" onclick="selectPest('${r.pest.replace(/'/g, "\\'")}')">
            <div class="sc-crop">${data.crop}</div>
            <div class="sc-pest">${r.pest}</div>
            <div class="sc-bar-bg"><div class="sc-bar-fill ${fillClass(r.severity)}" style="width:0%" data-w="${r.score}%"></div></div>
            <div class="sc-footer">
                <div class="sc-score">${r.score}<small style="font-size:.55em;font-weight:400">/100</small></div>
                <span class="sc-sev sev-${sevClass(r.severity)}">${r.severity}</span>
            </div>
        </div>
    `).join('');

    setTimeout(() => {
        document.querySelectorAll('.sc-bar-fill').forEach(el => el.style.width = el.dataset.w);
    }, 100);
}

function renderDistrictBanners(alerts) {
    const bannerContainer = document.getElementById('banners');
    if (!bannerContainer) return;

    const confirmed = alerts.filter(a => a.confirmed || a.max_severity === 'Critical');
    if (confirmed.length === 0) {
        bannerContainer.innerHTML = '';
        return;
    }

    bannerContainer.innerHTML = confirmed.map(a => `
        <div class="alert-banner ${bannerClass(a.max_severity)}">
            <div class="ab-icon">${a.max_severity === 'Critical' ? '🚨' : '⚠️'}</div>
            <div>
                <div class="ab-title">${a.max_severity}: ${a.pest} outbreak reported in your district</div>
                <div class="ab-body">Confirmed by ${a.report_count} nearby farmers. Inspect your fields immediately.</div>
            </div>
        </div>
    `).join('');
}

function selectPest(name) {
    const risk = currentData.risks.find(r => r.pest === name);
    if (!risk) return;

    const panel = document.getElementById('detail-panel');
    if (!panel) return;

    if (selectedPestName === name) {
        panel.style.display = 'none';
        selectedPestName = null;
        return;
    }

    selectedPestName = name;
    panel.style.display = 'block';

    const icons = { 'Critical': '🚨', 'High': '⚠️', 'Medium': '🔶', 'Low': '✅' };
    const triggersHtml = risk.triggered_by.length
        ? `<ul class="triggers-list">${risk.triggered_by.map(t => `<li><span class="trigger-dot"></span>${t}</li>`).join('')}</ul>`
        : `<p style="font-size:.8rem;color:var(--muted)">No specific weather triggers identified.</p>`;

    panel.innerHTML = `
        <div class="detail-top">
            <div class="detail-icon">${icons[risk.severity] || '🌿'}</div>
            <div>
                <div class="detail-pest">${risk.pest}</div>
                <div class="detail-sub">${risk.severity} Risk · Score ${risk.score}/100</div>
            </div>
        </div>
        <div class="detail-body">
            <div class="detail-row">
                <div class="detail-box">
                    <div class="db-label">Recommended action</div>
                    <div class="db-val">${risk.treatment}</div>
                </div>
                <div class="detail-box">
                    <div class="db-label">Suggested Pesticide</div>
                    <div class="db-val">${risk.pesticide}</div>
                </div>
            </div>
            <div class="db-label" style="margin-bottom:.5rem;">Weather Analysis</div>
            ${triggersHtml}
        </div>
    `;
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function submitReport() {
    const crop = document.getElementById('r-crop').value;
    const pest = document.getElementById('r-pest').value;
    const severity = document.getElementById('r-severity').value;
    const btn = document.getElementById('btn-submit');

    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Submitting...';
    }

    try {
        await api.request('/pest/report', {
            method: 'POST',
            body: JSON.stringify({
                crop,
                pest_name: pest,
                severity,
                lat: 32.57,
                lon: 74.08
            })
        });

        showPestToast('✅ Sighting reported. Thank you for helping the community!');
        const locInput = document.getElementById('r-location');
        if (locInput) locInput.value = '';
    } catch (err) {
        showPestToast(err.message, true);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = '📤 Submit Report — رپورٹ کریں';
        }
    }
}

function showPestToast(msg, isErr = false) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.className = 'toast show' + (isErr ? ' err' : '');
    setTimeout(() => t.className = 'toast', 4000);
}

document.addEventListener('DOMContentLoaded', initPestAlerts);
