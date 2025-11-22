# reception_panel/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Notification(models.Model):
    """
    مدل اعلان‌های سیستم.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name=_("کاربر")
    )
    
    message = models.CharField(max_length=255, verbose_name=_("متن پیام"))
    
    link = models.URLField(
        blank=True, 
        null=True, 
        verbose_name=_("لینک"),
        help_text=_("لینک ارجاع (اختیاری)")
    )
    
    is_read = models.BooleanField(default=False, verbose_name=_("خوانده شده"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("زمان ایجاد"))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("اعلان")
        verbose_name_plural = _("اعلان‌ها")

    def __str__(self):
        return f"{self.user.username}: {self.message[:30]}"