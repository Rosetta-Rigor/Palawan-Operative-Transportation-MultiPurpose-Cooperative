// ============================================================================
// NOTIFICATION DROPDOWN FUNCTIONALITY
// ============================================================================

(function() {
    'use strict';
    
    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        const bellBtn = document.getElementById('notificationBellBtn');
        const dropdown = document.getElementById('notificationDropdown');
        
        if (!bellBtn || !dropdown) {
            console.warn('Notification elements not found');
            return;
        }
        
        // Toggle dropdown on bell click
        bellBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdown.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target) && e.target !== bellBtn) {
                dropdown.classList.remove('show');
            }
        });
        
        // Prevent dropdown from closing when clicking inside
        dropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
        
        // Mark notification as read when clicked
        const notificationItems = dropdown.querySelectorAll('.notification-item');
        notificationItems.forEach(function(item) {
            item.addEventListener('click', function(e) {
                const notificationId = this.getAttribute('data-notification-id');
                
                if (notificationId && this.classList.contains('unread')) {
                    // Send AJAX request to mark as read
                    fetch('/notifications/' + notificationId + '/mark-read/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    }).then(function(response) {
                        if (response.ok) {
                            // Remove unread styling
                            item.classList.remove('unread');
                            const unreadDot = item.querySelector('.notification-unread-dot');
                            if (unreadDot) {
                                unreadDot.remove();
                            }
                            
                            // Update badge count
                            updateNotificationCount();
                        }
                    }).catch(function(error) {
                        console.error('Error marking notification as read:', error);
                    });
                }
            });
        });
        
        // Update notification count
        function updateNotificationCount() {
            fetch('/api/notification-count/')
                .then(function(response) {
                    return response.json();
                })
                .then(function(data) {
                    const badge = bellBtn.querySelector('.notification-badge');
                    
                    if (data.count > 0) {
                        if (badge) {
                            badge.textContent = data.count;
                        } else {
                            // Create badge if it doesn't exist
                            const newBadge = document.createElement('span');
                            newBadge.className = 'notification-badge';
                            newBadge.textContent = data.count;
                            bellBtn.appendChild(newBadge);
                        }
                    } else {
                        // Remove badge if count is 0
                        if (badge) {
                            badge.remove();
                        }
                    }
                })
                .catch(function(error) {
                    console.error('Error fetching notification count:', error);
                });
        }
        
        // Poll for new notifications every 30 seconds
        setInterval(function() {
            updateNotificationCount();
        }, 30000);
        
        // Helper function to get CSRF token
        function getCookie(name) {
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
    });
})();
