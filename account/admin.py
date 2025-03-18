from datetime import timedelta
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from account.models import (
    CustomUser, Role, Department, UserProfile,
    EmailVerificationCode, PasswordResetCode, PendingProfileChange
)
from django.utils import timezone

from .forms import CustomUserCreationForm
from .tasks import send_new_user_welcome_email


# ----------------------------
# Department Admin
# ----------------------------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)


# ----------------------------
# Role Admin
# ----------------------------
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'department', 'group')
    search_fields = ('name',)
    list_filter = ('department',)
    ordering = ('name',)


# ----------------------------
# UserProfile Inline
# ----------------------------
# Inline for UserProfile to edit profile details along with the user.
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"
    fieldsets = (
        (None, {
            'fields': ('date_of_birth', 'ghana_card_number', 'profile_picture', 'rating')
        }),
    )


class DepartmentListFilter(admin.SimpleListFilter):
    title = 'Department'
    parameter_name = 'department'

    def lookups(self, request, model_admin):
        departments = Department.objects.all()
        return [(dept.id, dept.name) for dept in departments]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(roles__department__id=self.value()).distinct()
        return queryset


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm  # Use our custom add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'username', 'roles')
        }),
    )
    fieldsets = (
        ('Official Info', {
            'fields': ('first_name', 'last_name', 'email', 'password', 'username', 'roles')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
        }),
    )
    list_display = ('email', 'username', 'is_staff', 'get_roles', 'get_departments')
    search_fields = ('email', 'username')
    ordering = ('email',)
    filter_horizontal = ('roles',)
    list_filter = ('roles', DepartmentListFilter)

    def get_roles(self, obj):
        # Display roles as comma-separated list
        return ", ".join([role.name for role in obj.roles.all()])

    get_roles.short_description = "Roles"

    def get_departments(self, obj):
        # Display the departments (via roles) as a unique list
        departments = {role.department.name for role in obj.roles.all() if role.department}
        return ", ".join(departments)

    get_departments.short_description = "Departments"

    def save_model(self, request, obj, form, change):
        """
        After saving, trigger a background task to send the user a password reset email.
        """
        super().save_model(request, obj, form, change)
        # Trigger the email task only when creating a new user (not on change)
        if not change:
            from account.tasks import send_password_reset_code_email  # import your task
            send_new_user_welcome_email.delay(obj.pk)


# ----------------------------
# Signal to Sync Roles with Groups
# ----------------------------
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


@receiver(m2m_changed, sender=CustomUser.roles.through)
def sync_user_groups_with_roles(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Whenever the 'roles' ManyToMany relationship changes for a CustomUser,
    add or remove the user to/from the corresponding Django Groups.
    """
    if action == 'post_add':
        for role_pk in pk_set:
            try:
                role = Role.objects.get(pk=role_pk)
                if role.group:
                    instance.groups.add(role.group)
            except Role.DoesNotExist:
                continue
    elif action == 'post_remove':
        for role_pk in pk_set:
            try:
                role = Role.objects.get(pk=role_pk)
                if role.group:
                    instance.groups.remove(role.group)
            except Role.DoesNotExist:
                continue
