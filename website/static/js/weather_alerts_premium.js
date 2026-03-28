/* ── Premium Weather Alerts Scripts ── */

async function initWeather() {
    if (!api.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }

    const lat = 32.57; // Gujrat, Pakistan
    const lon = 74.08;

    try {
        const data = await api.request(`/pest/weather?lat=${lat}&lon=${lon}&days=7`);
        renderWeather(data);
    } catch (err) {
        showToast('Failed to load weather data', true);
        console.error(err);
    }
}

function renderWeather(data) {
    const s = data.summary;
    
    // Summary cards
    document.getElementById('avg-temp').textContent = `${s.temp_mean.toFixed(1)}°C`;
    document.getElementById('max-temp').textContent = `${s.temp_max.toFixed(1)}°C`;
    document.getElementById('avg-rh').textContent = `${s.humidity_avg.toFixed(0)}%`;
    document.getElementById('total-rain').textContent = `${s.rain_total.toFixed(1)}mm`;
    
    document.getElementById('location-label').innerHTML = `<i class="fas fa-map-marker-alt"></i> Gujrat, Punjab (32.57, 74.08)`;

    // Alerts
    const alertsList = document.getElementById('weather-alerts-list');
    if (data.alerts && data.alerts.length > 0) {
        alertsList.innerHTML = data.alerts.map(a => `
            <div class="alert-item alert-${a.type}">
                <div class="alert-icon">
                    ${a.type === 'critical' ? '🚨' : a.type === 'warning' ? '⚠️' : 'ℹ️'}
                </div>
                <div class="alert-content">
                    <div class="alert-title">${a.title}</div>
                    <div class="alert-body">${a.body}</div>
                </div>
            </div>
        `).join('');
    } else {
        alertsList.innerHTML = `
            <div style="text-align:center; padding: 2rem 1rem; color: var(--muted);">
                <i class="fas fa-check-circle" style="color:var(--green); font-size:1.5rem; margin-bottom:1rem; display:block;"></i>
                <p style="font-size:0.85rem;">No critical weather hazards detected for the next 7 days.</p>
            </div>
        `;
    }

    // Mock 7-day forecast items for visuals
    const forecast = document.getElementById('forecast-container');
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const icons = ['☀️', '🌤️', '⛅', '🌦️', '🌧️', '⛈️', '🌥️'];
    const today = new Date().getDay();
    
    forecast.innerHTML = Array.from({length: 7}).map((_, i) => {
        const dIdx = (today + i) % 7;
        const icon = i === 0 ? '☀️' : icons[Math.floor(Math.random() * icons.length)];
        const t = (s.temp_mean + (Math.random() * 4 - 2)).toFixed(0);
        return `
            <div class="day-item">
                <div class="day-name">${i === 0 ? 'Today' : days[dIdx]}</div>
                <div class="day-icon">${icon}</div>
                <div class="day-temp">${t}°C</div>
                <div class="day-rain">${(Math.random() * 5).toFixed(1)}mm</div>
            </div>
        `;
    }).join('');
}

function showToast(msg, isErr = false) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.className = 'toast show' + (isErr ? ' error' : '');
    setTimeout(() => t.className = 'toast', 4000);
}

document.addEventListener('DOMContentLoaded', initWeather);
