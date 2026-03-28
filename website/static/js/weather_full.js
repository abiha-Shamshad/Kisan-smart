/* ── Weather Monitor Full JS ── */

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const WEATHER_ICONS = ['☀️', '🌤️', '⛅', '🌦️', '🌧️', '⛈️', '🌥️', '🌨️'];

async function initWeatherMonitor() {
    const lat = 32.57, lon = 74.08, days = 7;
    try {
        const data = await api.request(`/pest/weather?lat=${lat}&lon=${lon}&days=${days}`);
        renderSummary(data.summary);
        renderForecast(data.summary);
        renderHazards(data.alerts);
        renderAdvisories(data.summary);
        renderImpactGrid(data.summary);
    } catch (err) {
        showToast(err.message, true);
    }
}

function renderSummary(s) {
    document.getElementById('avg-temp').textContent = `${s.temp_mean.toFixed(1)}°C`;
    document.getElementById('max-temp').textContent = `${s.temp_max.toFixed(1)}°C`;
    document.getElementById('avg-rh').textContent = `${s.humidity_avg.toFixed(0)}%`;
    document.getElementById('total-rain').textContent = `${s.rain_total.toFixed(1)}mm`;
}

function renderForecast(s) {
    const today = new Date().getDay();
    document.getElementById('forecast-grid').innerHTML = Array.from({ length: 7 }, (_, i) => {
        const dIdx = (today + i) % 7;
        const icon = i === 0 ? '☀️' : WEATHER_ICONS[Math.floor(Math.random() * 6)];
        const temp = (s.temp_mean + (Math.random() * 6 - 3)).toFixed(0);
        const rain = (Math.random() * (s.rain_total / 7) * 2).toFixed(1);
        return `
            <div class="text-center bg-gray-50 hover:bg-blue-50 rounded-2xl p-3 transition-all cursor-default">
                <div class="text-xs font-bold text-gray-400 uppercase tracking-wide mb-1.5">${i === 0 ? 'Today' : DAYS[dIdx]}</div>
                <div class="text-2xl mb-1.5">${icon}</div>
                <div class="font-syne font-black text-gray-800 text-base">${temp}°</div>
                <div class="text-xs text-blue-400 mt-0.5">${rain}mm</div>
            </div>
        `;
    }).join('');
}

function renderHazards(alerts) {
    const list = document.getElementById('hazards-list');
    if (!alerts || !alerts.length) {
        list.innerHTML = `
            <div class="bg-green-50 border border-green-200 rounded-2xl p-5 text-center">
                <div class="text-3xl mb-2">✅</div>
                <div class="font-bold text-sm text-green-800 mb-1">All Clear</div>
                <div class="text-xs text-green-600">No significant weather hazards detected for the next 7 days.</div>
            </div>`;
        return;
    }

    const typeMap = {
        critical: { bg: 'bg-red-50 border-red-200', icon: '🚨', textColor: 'text-red-800', subColor: 'text-red-600', dot: 'bg-red-500' },
        warning:  { bg: 'bg-amber-50 border-amber-200', icon: '⚠️', textColor: 'text-amber-900', subColor: 'text-amber-700', dot: 'bg-amber-400' },
        info:     { bg: 'bg-blue-50 border-blue-200', icon: 'ℹ️', textColor: 'text-blue-900', subColor: 'text-blue-600', dot: 'bg-blue-400' },
    };

    list.innerHTML = alerts.map(a => {
        const t = typeMap[a.type] || typeMap.info;
        return `
            <div class="${t.bg} border rounded-2xl p-4 flex gap-3 items-start">
                <span class="text-xl flex-shrink-0">${t.icon}</span>
                <div>
                    <div class="font-bold text-sm ${t.textColor} mb-0.5">${a.title}</div>
                    <div class="text-xs ${t.subColor} leading-relaxed">${a.body}</div>
                </div>
            </div>
        `;
    }).join('');
}

function renderAdvisories(s) {
    // Spraying window
    let sprayIcon = '✅', sprayText = 'Conditions suitable for spraying';
    if (s.rain_total > 20) { sprayIcon = '❌'; sprayText = 'Avoid spraying — heavy rain forecast'; }
    else if (s.humidity_avg > 80) { sprayIcon = '⚠️'; sprayText = 'High humidity — spray early morning'; }

    // Irrigation
    let irrIcon = '💦', irrText = 'Regular irrigation recommended';
    if (s.rain_total > 40) { irrIcon = '🚫'; irrText = 'Skip irrigation — sufficient rainfall'; }
    else if (s.temp_max > 40) { irrIcon = '🔴'; irrText = 'Increase irrigation — extreme heat'; }

    // Fungal risk
    let funIcon = '✅', funText = 'Low fungal risk this week';
    if (s.humidity_avg > 80 && s.temp_mean > 20) { funIcon = '🍄'; funText = 'High fungal risk — apply fungicide'; }
    else if (s.humidity_avg > 70) { funIcon = '⚠️'; funText = 'Moderate risk — monitor closely'; }

    document.getElementById('spray-icon').textContent = sprayIcon;
    document.getElementById('spray-advice').textContent = sprayText;
    document.getElementById('irr-icon').textContent = irrIcon;
    document.getElementById('irr-advice').textContent = irrText;
    document.getElementById('fungal-icon').textContent = funIcon;
    document.getElementById('fungal-advice').textContent = funText;
}

function renderImpactGrid(s) {
    const impacts = [
        {
            pest: 'Yellow Rust',
            icon: '🌾',
            level: s.humidity_avg > 75 && s.temp_mean < 25 ? 'High' : 'Low',
            reason: `Humidity ${s.humidity_avg.toFixed(0)}% — ${s.humidity_avg > 75 ? 'ideal for rust' : 'below threshold'}`,
        },
        {
            pest: 'Rice Blast',
            icon: '🌱',
            level: s.humidity_avg > 80 ? 'High' : 'Moderate',
            reason: `Warm nights + ${s.humidity_avg.toFixed(0)}% RH ${s.humidity_avg > 80 ? 'create ideal conditions' : 'moderate pressure'}`,
        },
        {
            pest: 'Whitefly',
            icon: '🪲',
            level: s.temp_max > 38 ? 'High' : 'Low',
            reason: `Max temp ${s.temp_max.toFixed(1)}°C — ${s.temp_max > 38 ? 'hot & dry favors whitefly' : 'below preference threshold'}`,
        },
        {
            pest: 'Locust',
            icon: '🦗',
            level: s.rain_total < 5 && s.temp_max > 35 ? 'Moderate' : 'Low',
            reason: `Dry conditions ${s.rain_total < 5 ? 'increase migration risk' : '— adequate rain reduces risk'}`,
        },
    ];

    const colors = { High: 'border-red-200 bg-red-50', Moderate: 'border-amber-200 bg-amber-50', Low: 'border-green-200 bg-green-50' };
    const textC  = { High: 'text-red-600', Moderate: 'text-amber-600', Low: 'text-green-600' };

    document.getElementById('impact-grid').innerHTML = impacts.map(it => `
        <div class="${colors[it.level]} border rounded-2xl p-4">
            <div class="text-2xl mb-2">${it.icon}</div>
            <div class="font-syne font-bold text-sm text-gray-900 mb-0.5">${it.pest}</div>
            <div class="text-xs font-bold ${textC[it.level]} mb-1">${it.level} Pressure</div>
            <div class="text-xs text-gray-400 leading-relaxed">${it.reason}</div>
        </div>
    `).join('');
}

function showToast(msg, isErr = false) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.className = `fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl text-white text-sm font-semibold shadow-xl ${isErr ? 'bg-red-500' : 'bg-blue-600'}`;
    setTimeout(() => t.className = 'fixed bottom-6 right-6 z-50 hidden', 4500);
}

document.addEventListener('DOMContentLoaded', initWeatherMonitor);
