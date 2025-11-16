# reception_panel/models.py
"""
مدل‌های اختصاصی اپلیکیشن reception_panel.
"""

from django.db import models
from django.conf import settings

# --- مدل اعلان (نوتیفیکیشن) ---
class Notification(models.Model):
    """
    مدل ذخیره‌سازی اعلان‌های درون‌برنامه‌ای برای کاربران.
    این مدل هم برای بیماران و هم برای کارمندان استفاده می‌شود.
    """
    
    # کاربری که این اعلان را دریافت می‌کند
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    
    message = models.CharField(max_length=255, verbose_name="متن پیام")
    
    link = models.URLField(
        blank=True, 
        null=True, 
        verbose_name="لینک (اختیاری)",
        help_text="لینکی که کاربر پس از کلیک به آن هدایت می‌شود (مثلاً لینک مشاوره یا نوبت)"
    )
    
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")

    class Meta:
        ordering = ['-created_at']  # اعلان‌های جدیدتر بالاتر نمایش داده می‌شوند
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:30]}"