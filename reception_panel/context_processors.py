# reception_panel/context_processors.py
"""
این فایل شامل Context Processors سفارشی است که
متغیرهایی را به صورت خودکار به "تمام" تمپلیت‌های
پروژه اضافه می‌کنند.
"""

from .models import Notification

def unread_notifications(request):
    """
    یک پردازشگر زمینه (Context Processor) که تعداد اعلان‌های
    خوانده نشده و لیست آخرین اعلان‌ها را به کانتکست (context)
    تمامی صفحات اضافه می‌کند.
    
    این تابع در 'settings.base.TEMPLATES' ثبت شده است.
    """
    # این پردازشگر فقط برای کاربرانی که لاگین کرده‌اند اجرا می‌شود
    if request.user.is_authenticated:
        
        # ۱. محاسبه تعداد خوانده نشده‌ها (برای نمایش Badge)
        unread_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        
        # ۲. واکشی ۵ اعلان آخر (برای نمایش در Dropdown)
        latest_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        
        # این دیکشنری با کانتکست اصلی تمپلیت ادغام می‌شود
        return {
            'unread_notification_count': unread_count,
            'latest_notifications': latest_notifications
        }
    
    # اگر کاربر لاگین نکرده باشد، دیکشنری خالی برگردان
    return {}