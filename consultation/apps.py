# consultation/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ConsultationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'consultation'
    verbose_name = _("مدیریت مشاوره‌ها")