# reception_panel/decorators.py
"""
دکوریتورهای اختصاصی پنل پذیرش.
"""

from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect

def staff_required(view_func=None, login_url=None):
    """
    دکوریتور بررسی دسترسی کارمند (Staff).
    کاربر باید لاگین کرده و is_staff=True باشد.
    """
    if login_url is None:
        login_url = reverse_lazy('reception_panel:login')

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url=login_url
    )
    
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator