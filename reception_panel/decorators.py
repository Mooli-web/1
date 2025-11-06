from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy

def staff_required(view_func=None, login_url=None):
    """
    Decorator for views that checks that the user is logged in and is a staff member.
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
