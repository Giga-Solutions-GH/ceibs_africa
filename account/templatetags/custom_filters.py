# your_app/templatetags/custom_filters.py
from django import template

register = template.Library()


@register.filter
def has_role(user, role_dept):
    """
    Check if the user has a specific role within a specific department.
    The argument should be a comma-separated string: "RoleName,DepartmentName".

    Example usage in template:
        {% if request.user|has_role:"Facilitator,Programs" %}
            <!-- Show facilitator links -->
        {% endif %}
    """
    try:
        role_name, dept_name = role_dept.split(',')
        role_name = role_name.strip()
        dept_name = dept_name.strip()
    except ValueError:
        # If the argument is not properly formatted, return False.
        return False

    # Use the has_role method defined on your CustomUser model.
    return user.has_role(role_name, dept_name)
