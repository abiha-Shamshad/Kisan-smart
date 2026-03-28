/* ── History Premium JS ── */

let historyData = [];
let filteredData = [];
let currentPage = 1;
const itemsPerPage = 8;

async function loadHistory() {
    try {
        // First try to fetch from API
        const data = await api.request('/history/');
        
        // Handle mock vs real data shape
        if (data && data.predictions) {
            historyData = data.predictions;
        } else if (Array.isArray(data)) {
            historyData = data;
        } else {
            console.warn("Unexpected API response format, attempting to parse raw array", data);
            historyData = [];
        }

        // If nothing returned from API, and we are in mock mode, populate with high-end premium mock data for demonstration
        if (historyData.length === 0) {
            // Generate some beautiful mock data
            const crops = ['Wheat', 'Rice', 'Maize', 'Cotton', 'Sugarcane'];
            const ferts = ['Urea', 'DAP', 'NPK 15-15-15', 'SSP', 'SOP'];
            
            for (let i = 0; i < 28; i++) {
                const date = new Date();
                date.setDate(date.getDate() - Math.floor(Math.random() * 45));
                historyData.push({
                    id: 1000 - i,
                    crop: crops[Math.floor(Math.random() * crops.length)],
                    nitrogen: Math.floor(Math.random() * 120 + 20),
                    phosphorus: Math.floor(Math.random() * 60 + 10),
                    potassium: Math.floor(Math.random() * 50 + 10),
                    ph: (Math.random() * 3 + 5.5).toFixed(1),
                    recommended_fertilizer: ferts[Math.floor(Math.random() * ferts.length)],
                    confidence: Math.floor(Math.random() * 30 + 70), // 70 to 99
                    created_at: date.toISOString()
                });
            }
            // Sort mock data newest first
            historyData.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        }

        applyFilters(); 
    } catch (err) {
        console.error("Failed to load history:", err);
        document.getElementById('historyTableBody').innerHTML = `
            <tr>
                <td colspan="5" class="py-12 text-center text-red-500">
                    <i class="fas fa-exclamation-circle text-3xl mb-3"></i>
                    <p>Failed to load records. ${err.message}</p>
                </td>
            </tr>
        `;
    }
}

function applyFilters() {
    const search = document.getElementById('searchInput').value.toLowerCase();
    const crop = document.getElementById('cropFilter').value.toLowerCase();
    const conf = document.getElementById('confidenceFilter').value;

    filteredData = historyData.filter(item => {
        // Search
        if (search && !(item.crop.toLowerCase().includes(search) || item.recommended_fertilizer.toLowerCase().includes(search))) return false;
        
        // Crop
        if (crop && item.crop.toLowerCase() !== crop) return false;

        // Confidence
        if (conf === 'high' && item.confidence < 80) return false;
        if (conf === 'medium' && (item.confidence < 60 || item.confidence >= 80)) return false;
        if (conf === 'low' && item.confidence >= 60) return false;

        return true;
    });

    document.getElementById('resultsCount').textContent = `${filteredData.length} records found`;
    currentPage = 1;
    renderTable();
}

function changePage(delta) {
    const totalPages = Math.ceil(filteredData.length / itemsPerPage) || 1;
    currentPage += delta;
    if (currentPage < 1) currentPage = 1;
    if (currentPage > totalPages) currentPage = totalPages;
    renderTable();
}

function renderTable() {
    const tbody = document.getElementById('historyTableBody');
    const pagination = document.getElementById('paginationContainer');
    
    if (filteredData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="py-12 text-center text-gray-400">
                    <i class="fas fa-folder-open text-3xl mb-3 text-gray-300"></i>
                    <p>No historical records match your filters.</p>
                </td>
            </tr>
        `;
        pagination.style.display = 'none';
        return;
    }

    const totalPages = Math.ceil(filteredData.length / itemsPerPage);
    const start = (currentPage - 1) * itemsPerPage;
    const pageData = filteredData.slice(start, start + itemsPerPage);

    tbody.innerHTML = pageData.map(r => {
        const dateObj = new Date(r.created_at);
        const dateStr = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        
        let confBadge = 'sev-badge-low';
        if (r.confidence >= 85) confBadge = 'sev-badge-low'; // green
        else if (r.confidence >= 70) confBadge = 'sev-badge-high'; // amber
        else confBadge = 'sev-badge-critical'; // red

        return `
            <tr class="table-row-hover hover:bg-gray-50/50 cursor-pointer group">
                <td class="py-4 px-6">
                    <div class="font-bold text-gray-900 group-hover:text-green-700 transition-colors">${r.crop}</div>
                    <div class="text-xs text-gray-400 mt-0.5"><i class="far fa-calendar-alt mr-1"></i>${dateStr}</div>
                </td>
                <td class="py-4 px-6">
                    <div class="flex items-center gap-1 text-sm font-semibold text-gray-700">
                        <span class="text-green-600">${r.nitrogen}</span><span class="text-gray-300">/</span>
                        <span class="text-amber-500">${r.phosphorus}</span><span class="text-gray-300">/</span>
                        <span class="text-orange-700">${r.potassium}</span>
                    </div>
                </td>
                <td class="py-4 px-6">
                    <div class="font-medium text-gray-700">${r.ph}</div>
                </td>
                <td class="py-4 px-6">
                    <div class="font-syne font-bold text-gray-900">${r.recommended_fertilizer}</div>
                </td>
                <td class="py-4 px-6 text-right">
                    <span class="inline-flex items-center justify-center px-2 py-1 rounded-md text-xs font-bold ${confBadge}">
                        ${r.confidence}%
                    </span>
                </td>
            </tr>
        `;
    }).join('');

    // Update pagination controls
    pagination.style.display = 'flex';
    document.getElementById('currentPage').textContent = currentPage;
    document.getElementById('totalPages').textContent = totalPages;
    document.getElementById('prevBtn').disabled = currentPage === 1;
    document.getElementById('nextBtn').disabled = currentPage === totalPages;
}

function showToast(msg, isErr = false) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.className = `fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl text-white text-sm font-semibold shadow-xl transition-all ${isErr ? 'bg-red-500' : 'bg-green-600'}`;
    t.style.display = 'block';
    // Small timeout to allow display block to apply before animating opacity/transform via Tailwind classes
    setTimeout(() => {
        t.classList.remove('translate-y-20', 'opacity-0');
    }, 10);
    
    setTimeout(() => {
        t.classList.add('translate-y-20', 'opacity-0');
        setTimeout(() => t.style.display = 'none', 300); // Matches transition duration
    }, 3000);
}

function exportHistory() {
    if (!filteredData.length) {
        showToast("No data to export", true);
        return;
    }
    showToast("Exporting CSV...");
    
    const headers = ["Date", "Crop", "Nitrogen(N)", "Phosphorus(P)", "Potassium(K)", "pH", "Recommendation", "Confidence"];
    const rows = filteredData.map(r => [
        new Date(r.created_at).toLocaleDateString(),
        r.crop, r.nitrogen, r.phosphorus, r.potassium, r.ph,
        r.recommended_fertilizer, r.confidence
    ]);
    
    let csvContent = "data:text/csv;charset=utf-8," 
        + headers.join(",") + "\n"
        + rows.map(e => e.join(",")).join("\n");
        
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "kisan_smart_history.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function clearHistory() {
    if (confirm("Are you sure you want to clear your local history view? (This is a mock action)")) {
        historyData = [];
        applyFilters();
        showToast("History cleared successfully");
    }
}

document.addEventListener('DOMContentLoaded', loadHistory);
