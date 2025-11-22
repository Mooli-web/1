#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    # به صورت پیش‌فرض از تنظیمات local استفاده می‌کند (برای راحتی در توسعه)
    # در سرور، متغیر محیطی DJANGO_SETTINGS_MODULE مقداردهی می‌شود و این خط نادیده گرفته می‌شود.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_project.settings.local')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()