from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def role_required(role_name, department_name=None, redirect_url=None):
    """
    Decorator to ensure the logged-in user has a specified role (optionally in a specified department).
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.has_role(role_name, department_name):
                    return view_func(request, *args, **kwargs)
                return HttpResponseForbidden("You do not have the required role to access this page.")
            return redirect(redirect_url or 'account:login')

        return _wrapped_view

    return decorator


def department_required(department_name, redirect_url=None):
    """
    Decorator to ensure the logged-in user has any role in a given department.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.in_department(department_name):
                    return view_func(request, *args, **kwargs)
                return HttpResponseForbidden("You do not belong to the required department to access this page.")
            return redirect(redirect_url or 'account:login')

        return _wrapped_view

    return decorator
