// Renewal Buffer Zone JS
// Handles renewal modal, buffer zone, and member renewal actions

let renewedMembers = [];

function addToRenewed(vehicleId) {
	const eligibleList = document.getElementById('renewal-member-list');
	const renewedList = document.getElementById('renewed-member-list');
	const item = Array.from(eligibleList.children).find(li => li.querySelector('button') && li.querySelector('button').getAttribute('onclick').includes(vehicleId));
	if (item) {
		renewedMembers.push(vehicleId);
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
	renewedMembers.forEach(vehicleId => {
		fetch(`/members/${vehicleId}/renew/`, {
			method: 'POST',
			headers: {
				'X-CSRFToken': getCSRFToken(),
			},
		}).then(resp => {
			if (resp.ok) {
				location.reload();
			}
		});
	});
}

function getCSRFToken() {
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
	window.location.href = `/documents/add/${vehicleId}/`;
}

document.addEventListener('DOMContentLoaded', function() {
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
