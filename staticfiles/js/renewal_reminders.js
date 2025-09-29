// renewal_reminders.js
// Handles loading and color-coding of renewal reminders for dashboard

function getRenewalStatus(dateStr) {
    const today = new Date();
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

function loadBatchCards() {
    // Realistic placeholder batch data for dashboard
    const batches = [
        {
            batch: 'Batch 1',
            count: 23,
            renewal_date: '2025-10-15',
            members: ['Qiyana', 'Ezreal'],
            vehicles: ['ABC123', 'LMN456'],
            documents: ['OR 2025', 'CR 2025']
        },
        {
            batch: 'Batch 2',
            count: 17,
            renewal_date: '2025-11-20',
            members: ['Diana'],
            vehicles: ['XYZ789'],
            documents: ['Insurance']
        },
        {
            batch: 'Batch 3',
            count: 8,
            renewal_date: '2025-09-25',
            members: ['Qiyana'],
            vehicles: ['ABC123'],
            documents: ['CR 2025']
        }
    ];
    const row = document.getElementById('batch-cards-row');
    row.innerHTML = '';
    batches.forEach(b => {
        const status = getRenewalStatus(b.renewal_date);
        const card = document.createElement('div');
        card.className = 'col-md-4 mb-4';
        card.innerHTML = `
            <div class="card shadow-lg" style="border-left: 8px solid ${status.color};">
                <div class="card-body text-center">
                    <h3 class="card-title" style="font-size:2.2rem; margin-bottom:0.5rem;">${b.batch}</h3>
                    <div style="font-size:4rem; font-weight:bold; color:${status.color};">${b.count}</div>
                    <div style="margin-top:1rem; font-size:1.1rem; font-weight:500; color:${status.color};">
                        ${status.text}
                    </div>
                    <div style="font-size:0.95rem; color:#888;">Renewal: ${b.renewal_date}</div>
                    <div style="margin-top:1rem; font-size:0.95rem; color:#555;">
                        <strong>Members:</strong> ${b.members.join(', ')}<br>
                        <strong>Vehicles:</strong> ${b.vehicles.join(', ')}<br>
                        <strong>Documents:</strong> ${b.documents.join(', ')}
                    </div>
                </div>
            </div>
        `;
        row.appendChild(card);
    });
}

document.addEventListener('DOMContentLoaded', loadBatchCards);
