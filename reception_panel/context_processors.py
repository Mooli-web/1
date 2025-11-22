# reception_panel/context_processors.py
"""
Context Processors برای افزودن داده‌های سراسری به تمپلیت‌ها.
"""

from django.http import HttpRequest
from .models import Notification

def unread_notifications(request: HttpRequest) -> dict:
    """
    افزودن تعداد و لیست اعلان‌های خوانده نشده به کانتکست.
    """
    if request.user.is_authenticated:
        # بهینه‌سازی: استفاده از exists() اگر فقط چک کردن وجود مهم است،
        # اما اینجا تعداد دقیق را می‌خواهیم.
        unread_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        
        # دریافت ۵ اعلان آخر (خوانده شده یا نشده)
        latest_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        
        return {
            'unread_notification_count': unread_count,
            'latest_notifications': latest_notifications
        }
    
    return {}