# reception_panel/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ReceptionPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reception_panel'
    verbose_name = _("پنل پذیرش و مدیریت")