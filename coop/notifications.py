# coop/notifications.py
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


def create_notification(recipient, title, message, category, priority='normal', 
                       action_url=None, action_text=None, created_by=None,
                       related_object_type=None, related_object_id=None,
                       expires_in_days=None):
    """
    Utility function to create notifications consistently
    
    Args:
        recipient: User object who will receive the notification
        title: Short notification title (max 200 chars)
        message: Detailed notification message
        category: Notification category (see Notification.CATEGORY_CHOICES)
        priority: urgent, high, normal, or low (default: normal)
        action_url: Optional URL to redirect when clicked
        action_text: Optional text for action button
        created_by: User who triggered the notification (optional)
        related_object_type: Type of related object (e.g., 'member', 'vehicle')
        related_object_id: ID of related object
        expires_in_days: Number of days until notification expires
    
    Returns:
        Notification object
    """
    from .models import Notification
    
    expires_at = None
    if expires_in_days:
        expires_at = timezone.now() + timedelta(days=expires_in_days)
    
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        category=category,
        priority=priority,
        action_url=action_url,
        action_text=action_text,
        created_by=created_by,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
        expires_at=expires_at
    )


def notify_all_staff(title, message, category, priority='normal', 
                     action_url=None, action_text=None, created_by=None,
                     related_object_type=None, related_object_id=None):
    """
    Send notification to all staff members (admin/manager)
    
    Args:
        title: Notification title
        message: Notification message
        category: Notification category
        priority: urgent, high, normal, or low (default: normal)
        action_url: Optional URL to redirect when clicked
        action_text: Optional text for action button
        created_by: User who triggered the notification
        related_object_type: Type of related object (e.g., 'member', 'vehicle')
        related_object_id: ID of related object
    
    Returns:
        List of created Notification objects
    """
    staff_users = User.objects.filter(is_staff=True, is_active=True)
    notifications = []
    
    for staff in staff_users:
        notif = create_notification(
            recipient=staff,
            title=title,
            message=message,
            category=category,
            priority=priority,
            action_url=action_url,
            action_text=action_text,
            created_by=created_by,
            related_object_type=related_object_type,
            related_object_id=related_object_id
        )
        notifications.append(notif)
    
    return notifications


def get_unread_count(user):
    """
    Get unread notification count for user (excluding expired)
    
    Args:
        user: User object
    
    Returns:
        Integer count of unread notifications
    """
    from .models import Notification
    
    return Notification.objects.filter(
        recipient=user,
        is_read=False
    ).exclude(
        expires_at__lt=timezone.now()
    ).count()


def mark_all_as_read(user):
    """
    Mark all notifications as read for user
    
    Args:
        user: User object
    
    Returns:
        Number of notifications marked as read
    """
    from .models import Notification
    
    return Notification.objects.filter(
        recipient=user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())


def delete_old_notifications(days=30):
    """
    Delete read notifications older than X days
    Management command utility
    
    Args:
        days: Number of days to keep read notifications (default: 30)
    
    Returns:
        Tuple of (count, dict) from queryset.delete()
    """
    from .models import Notification
    
    cutoff_date = timezone.now() - timedelta(days=days)
    return Notification.objects.filter(
        is_read=True,
        read_at__lt=cutoff_date
    ).delete()


def get_recent_notifications(user, limit=5):
    """
    Get recent notifications for user
    
    Args:
        user: User object
        limit: Maximum number of notifications to return (default: 5)
    
    Returns:
        QuerySet of Notification objects
    """
    from .models import Notification
    
    return Notification.objects.filter(
        recipient=user
    ).order_by('-created_at')[:limit]
