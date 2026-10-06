from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse


def customer_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.user.role != "customer":
            return HttpResponseForbidden("Customer accounts only.")
        return view_func(request, *args, **kwargs)
    return wrapped


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.user.role != "admin":
            return HttpResponseForbidden("Bank admin accounts only.")
        return view_func(request, *args, **kwargs)
    return wrapped


def json_post_required(view_func):
    """Small guard for the API mutation endpoints: POST only, JSON error on anything else."""
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "POST required."}, status=405)
        return view_func(request, *args, **kwargs)
    return wrapped
