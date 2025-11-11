/**
 * Admin Logs JavaScript - CLEAN VERSION
 * NO RIPPLE EFFECTS - NO TRANSFORM ACCUMULATION
 */

let searchTimeout = null;

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearch');
    const staffFilter = document.getElementById('staffFilter');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const value = this.value.trim();
            
            if (clearSearchBtn) {
                clearSearchBtn.style.display = value ? 'flex' : 'none';
            }
            
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (value.length >= 2 || value.length === 0) {
                    performSearch(value);
                }
            }, 500);
        });
        
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                clearTimeout(searchTimeout);
                performSearch(this.value.trim());
            }
        });
    }
    
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            if (searchInput) {
                searchInput.value = '';
                this.style.display = 'none';
                performSearch('');
            }
        });
    }
    
    if (staffFilter) {
        staffFilter.addEventListener('change', function() {
            const url = new URL(window.location.href);
            
            if (this.value) {
                url.searchParams.set('logged_by', this.value);
            } else {
                url.searchParams.delete('logged_by');
            }
            
            url.searchParams.delete('page');
            window.location.href = url.toString();
        });
    }
});

function filterByYear(year) {
    const url = new URL(window.location.href);
    
    if (year) {
        url.searchParams.set('carwash_year', year);
    } else {
        url.searchParams.delete('carwash_year');
    }
    
    url.searchParams.delete('page');
    window.location.href = url.toString();
}

function filterByPaymentYear(year) {
    const url = new URL(window.location.href);
    
    if (year) {
        url.searchParams.set('payment_year', year);
    } else {
        url.searchParams.delete('payment_year');
    }
    
    url.searchParams.delete('page');
    window.location.href = url.toString();
}

function performSearch(query) {
    const url = new URL(window.location.href);
    
    if (query) {
        url.searchParams.set('search', query);
    } else {
        url.searchParams.delete('search');
    }
    
    url.searchParams.delete('page');
    window.location.href = url.toString();
}

// ===== MODAL FUNCTIONS =====

function openFilterModal() {
    const modal = document.getElementById('filterModal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeFilterModal() {
    const modal = document.getElementById('filterModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function resetFilters() {
    const form = document.getElementById('filterForm');
    if (form) {
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (input.type === 'checkbox') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });
    }
}

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeFilterModal();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const modalContent = document.querySelector('.payment-logs-modal-content');
    if (modalContent) {
        modalContent.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }
});

function showLogDetail(logId) {
    console.log('Show detail for log:', logId);
}

function exportLogs(format) {
    console.log('Exporting logs in format:', format);
    alert(`Export feature coming soon! Format: ${format}`);
}

function printLogs() {
    window.print();
}

console.log('Admin Logs JS loaded - Clean version');
