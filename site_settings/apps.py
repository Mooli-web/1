from django.apps import AppConfig
# --- ADDED: Import specific errors ---
from django.db.utils import OperationalError
from django.core.exceptions import AppRegistryNotReady

class SiteSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'site_settings'
    verbose_name = "تنظیمات سایت"

    def ready(self):
        """
        Ensures the SiteSettings singleton instance exists when the app is ready.
        Catches OperationalError which occurs if this runs during the very first
        migration before the site_settings table is created.
        """
        try:
            # Import model locally to avoid circular imports
            SiteSettings = self.get_model('SiteSettings')
            # Use .load() which calls get_or_create
            SiteSettings.load()
        except (OperationalError, AppRegistryNotReady) as e:
            # این اتفاق در اولین اجرای 'migrate' طبیعی است،
            # چون هنوز جدولی ساخته نشده است.
            # می‌توانیم با خیال راحت از آن بگذریم.
            print(f"Skipping SiteSettings singleton check (normal during migrations): {e}")
        except Exception as e:
            # Handle other potential exceptions
            print(f"Could not load/create SiteSettings singleton: {e}")