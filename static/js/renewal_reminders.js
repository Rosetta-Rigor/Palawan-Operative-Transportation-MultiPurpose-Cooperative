// renewal_reminders.js
// Handles loading and color-coding of renewal reminders for dashboard

// Use Manila timezone for date calculations
function getManilaDate() {
    // Manila is UTC+8
    const now = new Date();
    // Get UTC time and add 8 hours
    return new Date(now.getTime() + (8 * 60 * 60 * 1000));
}

function getRenewalStatus(dateStr) {
    const today = getManilaDate();
    const renewalDate = new Date(dateStr);
    const diffMonths = (renewalDate.getFullYear() - today.getFullYear()) * 12 + (renewalDate.getMonth() - today.getMonth());
    if (diffMonths <= 0 && renewalDate < today) {
        return {color: 'gray', text: 'Expired'};
    } else if (diffMonths <= 1) {
        return {color: 'red', text: 'Renewal Very Soon'};
    } else if (diffMonths <= 2) {
        return {color: 'yellow', text: 'Renewal Approaching'};
    } else {
        return {color: 'green', text: 'OK'};
    }
}

// --- Batch Data ---
const batches = [
    {
        batch: 'Batch 1',
        count: 23,
        renewal_date: '2025-10-15',
        members: ['Qiyana', 'Ezreal', 'Kai', 'Lulu', 'Jinx', 'Vi', 'Jayce', 'Heimer', 'Caitlyn', 'Ekko', 'Camille', 'Viktor', 'Singed', 'Ziggs', 'Orianna', 'Blitz', 'Riven', 'Yasuo', 'Sona', 'Seraphine', 'Ez', 'Lux', 'Garen'],
        vehicles: ['ABC123', 'LMN456', 'XYZ111', 'DEF222'],
        documents: ['OR 2025', 'CR 2025', 'Insurance', 'Emission']
    },
    {
        batch: 'Batch 3',
        count: 17,
        renewal_date: '2025-11-20',
        members: ['Diana', 'Leona', 'Sivir', 'Talon', 'Shen', 'Akali', 'Kennen', 'Zed', 'Katarina', 'Draven', 'Darius', 'Swain', 'Vladimir', 'Sion', 'Urgot', 'Mordekaiser', 'Yone'],
        vehicles: ['XYZ789', 'QWE456'],
        documents: ['Insurance', 'OR 2025', 'CR 2025']
    },
    {
        batch: 'Batch 2',
        count: 8,
        renewal_date: '2025-09-25',
        members: ['Qiyana', 'Ezreal', 'Kai', 'Lulu', 'Jinx', 'Vi', 'Jayce', 'Heimer'],
        vehicles: ['ABC123', 'LMN456'],
        documents: ['CR 2025', 'Insurance']
    }
];

// --- Sorting and Filtering ---
function sortBatches(batches, sortBy) {
    if (sortBy === 'urgency') {
        // Sort by renewal urgency (Expired, Very Soon, Approaching, OK)
        return batches.slice().sort((a, b) => {
            const statusA = getRenewalStatus(a.renewal_date);
            const statusB = getRenewalStatus(b.renewal_date);
            const order = { 'red': 0, 'yellow': 1, 'gray': 2, 'green': 3 };
            return order[statusA.color] - order[statusB.color];
        });
    } else if (sortBy === 'renewal_date') {
        return batches.slice().sort((a, b) => new Date(a.renewal_date) - new Date(b.renewal_date));
    } else if (sortBy === 'members') {
        return batches.slice().sort((a, b) => b.members.length - a.members.length);
    }
    return batches;
}

function filterBatches(batches, filterMonth) {
    if (!filterMonth) return batches;
    // filterMonth is "YYYY-MM"
    return batches.filter(b => b.renewal_date.startsWith(filterMonth));
}

// --- Pagination ---
const MEMBERS_PER_PAGE = 8;
let currentPage = {};

function renderBatchCards() {
    const sortBy = document.getElementById('batch-sort').value;
    const filterMonth = document.getElementById('batch-filter').value;
    let batchList = sortBatches(batches, sortBy);
    batchList = filterBatches(batchList, filterMonth);
    const row = document.getElementById('batch-cards-row');
    row.innerHTML = '';
    batchList.forEach((b, batchIdx) => {
        if (currentPage[batchIdx] === undefined) currentPage[batchIdx] = 1;
        const status = getRenewalStatus(b.renewal_date);
        // Pagination for members
        const totalPages = Math.ceil(b.members.length / MEMBERS_PER_PAGE);
        const page = currentPage[batchIdx];
        const startIdx = (page - 1) * MEMBERS_PER_PAGE;
        const endIdx = startIdx + MEMBERS_PER_PAGE;
        const pagedMembers = b.members.slice(startIdx, endIdx);
        // Notification options placeholder
        const notifOptions = `<div class="mt-2 mb-2"><span class="badge badge-info">Account</span> <span class="badge badge-warning">Email</span> <span class="badge badge-success">Phone</span></div>`;
        // Card HTML
        const card = document.createElement('div');
        card.className = 'col-md-4 mb-4';
        card.innerHTML = `
            <div class="card shadow-lg" style="border-left: 8px solid ${status.color};">
                <div class="card-body">
                    <h3 class="card-title text-center" style="font-size:2.2rem; margin-bottom:0.5rem;">${b.batch}</h3>
                    <div class="text-center" style="font-size:4rem; font-weight:bold; color:${status.color};">${b.count}</div>
                    <div class="text-center" style="margin-top:1rem; font-size:1.1rem; font-weight:500; color:${status.color};">
                        ${status.text}
                    </div>
                    <div class="text-center" style="font-size:0.95rem; color:#888;">Renewal: ${b.renewal_date}</div>
                    ${notifOptions}
                    <div style="margin-top:1rem; font-size:0.95rem; color:#555;">
                        <strong>Members:</strong>
                        <ul style="list-style:none; padding-left:0; margin-bottom:0;">
                            ${pagedMembers.map(m => `<li>${m}</li>`).join('')}
                        </ul>
                        <div class="text-right" style="font-size:0.9rem; color:#888;">Page ${page} of ${totalPages}</div>
                        <div class="d-flex justify-content-center mt-2">
                            <button class="btn btn-sm btn-outline-primary mr-1" ${page === 1 ? 'disabled' : ''} onclick="changeMemberPage(${batchIdx}, ${page-1})">Prev</button>
                            <button class="btn btn-sm btn-outline-primary" ${page === totalPages ? 'disabled' : ''} onclick="changeMemberPage(${batchIdx}, ${page+1})">Next</button>
                        </div>
                        <hr>
                        <strong>Vehicles:</strong> ${b.vehicles.join(', ')}<br>
                        <strong>Documents:</strong> ${b.documents.join(', ')}
                    </div>
                </div>
            </div>
        `;
        row.appendChild(card);
    });
    renderBatchPagination(batchList);
}

function changeMemberPage(batchIdx, newPage) {
    currentPage[batchIdx] = newPage;
    renderBatchCards();
}

function renderBatchPagination(batchList) {
    // Optionally show batch-level pagination if needed (not per member)
    // For now, handled per batch card
    // Could add batch-level pagination here if batches > 3
}

function loadDashboardNotifications() {
    // Placeholder notifications for user compliance/upload/messages
    const notifications = [
        {type: 'success', message: 'Qiyana has uploaded all required documents for Batch 1.'},
        {type: 'warning', message: 'Diana has not yet uploaded Insurance for Batch 2.'},
        {type: 'info', message: 'Ezreal renewal approaching for Batch 1.'},
        {type: 'success', message: 'All vehicles in Batch 3 are compliant.'},
        {type: 'message', message: 'Admin: Please ensure all batches are updated before the end of the month.'},
        {type: 'message', message: 'System: New document types will be supported soon.'}
    ];
    const notifList = document.getElementById('dashboard-notif-list');
    notifList.innerHTML = '';
    notifications.forEach(n => {
        let color, icon;
        if (n.type === 'success') { color = '#43a047'; icon = '✔️'; }
        else if (n.type === 'warning') { color = '#ffa726'; icon = '⚠️'; }
        else if (n.type === 'info') { color = '#1976d2'; icon = 'ℹ️'; }
        else { color = '#333'; icon = '💬'; }
        const item = document.createElement('div');
        item.className = 'dashboard-notif-item';
        item.style.color = color;
        item.innerHTML = `<span style="font-size:1.3rem;">${icon}</span> <span>${n.message}</span>`;
        notifList.appendChild(item);
    });
}

function setupNotifToggle() {
    const notifCard = document.getElementById('dashboard-notif-card');
    const toggleBtn = document.getElementById('notif-toggle-btn');
    let minimized = false;
    toggleBtn.addEventListener('click', function() {
        minimized = !minimized;
        if (minimized) {
            notifCard.classList.add('minimized');
            toggleBtn.innerHTML = '&#x25BC;';
        } else {
            notifCard.classList.remove('minimized');
            toggleBtn.innerHTML = '&#x25B2;';
        }
    });
}


// --- Renewal Feature JS ---
let renewedMembers = [];

function addToRenewed(vehicleId) {
    // Move member from eligible list to renewed list
    const eligibleList = document.getElementById('renewal-member-list');
    const renewedList = document.getElementById('renewed-member-list');
    const item = Array.from(eligibleList.children).find(li => li.querySelector('button') && li.querySelector('button').getAttribute('onclick').includes(vehicleId));
    if (item) {
        renewedMembers.push(vehicleId);
        // Clone and add to renewed list
        const clone = item.cloneNode(true);
        clone.querySelector('button').remove();
        renewedList.appendChild(clone);
        item.remove();
    }
}

function confirmRenewal() {
    if (renewedMembers.length === 0) {
        alert('No members selected for renewal.');
        return;
    }
    if (!confirm('Are you sure you want to renew the selected members?')) return;
    // For each renewed member, send a POST request to backend to update renewal
    renewedMembers.forEach(vehicleId => {
        fetch(`/members/${vehicleId}/renew/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            },
        }).then(resp => {
            if (resp.ok) {
                // Optionally, reload page or update buffer zone
                location.reload();
            }
        });
    });
}

function getCSRFToken() {
    // Get CSRF token from cookies
    let name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showUpdateDocumentModal(vehicleId) {
    // Redirect to document add page for this vehicle and renewal date
    window.location.href = `/documents/add/${vehicleId}/`;
}

document.addEventListener('DOMContentLoaded', function() {
    // Setup sorting/filtering listeners
    document.getElementById('batch-sort').addEventListener('change', renderBatchCards);
    document.getElementById('batch-filter').addEventListener('change', renderBatchCards);
    renderBatchCards();
    loadDashboardNotifications();
    setupNotifToggle();
    // Renewal search filter
    const renewalSearch = document.getElementById('renewal-search');
    if (renewalSearch) {
        renewalSearch.addEventListener('input', function() {
            const val = this.value.toLowerCase();
            const items = document.querySelectorAll('#renewal-member-list li');
            items.forEach(li => {
                const text = li.textContent.toLowerCase();
                li.style.display = text.includes(val) ? '' : 'none';
            });
        });
    }
});
