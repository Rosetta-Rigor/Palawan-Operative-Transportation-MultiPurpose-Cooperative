// Batch Cards JS
// Handles sorting, filtering, and rendering of batch cards

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

function getManilaDate() {
	const now = new Date();
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

function sortBatches(batches, sortBy) {
	if (sortBy === 'urgency') {
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
	return batches.filter(b => b.renewal_date.startsWith(filterMonth));
}

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
		const totalPages = Math.ceil(b.members.length / MEMBERS_PER_PAGE);
		const page = currentPage[batchIdx];
		const startIdx = (page - 1) * MEMBERS_PER_PAGE;
		const endIdx = startIdx + MEMBERS_PER_PAGE;
		const pagedMembers = b.members.slice(startIdx, endIdx);
		const notifOptions = `<div class="mt-2 mb-2"><span class="badge badge-info">Account</span> <span class="badge badge-warning">Email</span> <span class="badge badge-success">Phone</span></div>`;
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

document.addEventListener('DOMContentLoaded', function() {
	document.getElementById('batch-sort').addEventListener('change', renderBatchCards);
	document.getElementById('batch-filter').addEventListener('change', renderBatchCards);
	renderBatchCards();
});
