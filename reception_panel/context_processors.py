# a_copy/reception_panel/context_processors.py

from .models import Notification

def unread_notifications(request):
    """
    Adds unread notification count and latest notifications to the context
    for all authenticated users.
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        
        latest_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5] # Get 5 most recent
        
        return {
            'unread_notification_count': unread_count,
            'latest_notifications': latest_notifications
        }
    return {}