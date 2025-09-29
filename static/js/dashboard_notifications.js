// Dashboard Notifications JS
// Handles loading and toggling of dashboard notifications

function loadDashboardNotifications() {
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

document.addEventListener('DOMContentLoaded', function() {
	loadDashboardNotifications();
	setupNotifToggle();
});
