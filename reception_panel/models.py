from django.db import models
from django.conf import settings

# --- ADDED: Notification Model ---
class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    message = models.CharField(max_length=255)
    link = models.URLField(blank=True, null=True) # لینک اختیاری به صفحه مربوطه
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:30]}"