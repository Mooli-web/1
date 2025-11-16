# reception_panel/decorators.py
"""
این فایل شامل دکوریتورهای (decorators) سفارشی برای پنل پذیرش است.
"""

from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy

def staff_required(view_func=None, login_url=None):
    """
    دکوریتور برای ویوهایی که نیاز به دسترسی "کارمند" (staff) دارند.
    
    این دکوریتور بررسی می‌کند که کاربر:
    1. لاگین کرده باشد (is_authenticated)
    2. عضو کارمندان باشد (is_staff)
    
    اگر کاربر این شروط را نداشته باشد، به صفحه لاگین پنل پذیرش
    (reception_panel:login) هدایت می‌شود.
    """
    if login_url is None:
        # آدرس صفحه لاگین مخصوص پنل پذیرش
        login_url = reverse_lazy('reception_panel:login')

    # استفاده از دکوریتور داخلی جنگو برای بررسی شرط
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url=login_url
    )
    
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator