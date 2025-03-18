from datetime import timedelta
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name='roles')

    def __str__(self):
        if self.department:
            return f"{self.name} ({self.department.name})"
        return self.name


@receiver(post_save, sender=Role)
def create_or_update_group_for_role(sender, instance, created, **kwargs):
    """
    Whenever a Role is created or updated, ensure there's a corresponding Django Group.
    """
    if created:
        # Create a new Group if it does not exist
        group, _ = Group.objects.get_or_create(name=instance.name)
        instance.group = group
        instance.save()
    else:
        # If Role name changed, update the Group name
        if instance.group and instance.group.name != instance.name:
            instance.group.name = instance.name
            instance.group.save()


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


# Create your models here.

# ----------------------------
# CustomUser Model
# ----------------------------
class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=356, null=True, blank=True)
    last_name = models.CharField(max_length=256, null=True, blank=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=250, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    USERNAME_FIELD = 'email'
    password1 = models.CharField(max_length=100, null=False, blank=False)
    password2 = models.CharField(max_length=100, null=False, blank=False)
    status_choices = (
        ("Active", "Active"),
        ("Inactive", "Inactive")
    )
    roles = models.ManyToManyField(Role, related_name='users', blank=True)
    status = models.CharField(max_length=100, null=False, blank=False, default="Active", choices=status_choices)
    active = models.BooleanField(default=True)
    flag = models.BooleanField(default=True)
    is_student = models.BooleanField(default=False, null=True, blank=True)
    email_verified = models.BooleanField(default=False)

    objects = CustomUserManager()

    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.username}"

    def has_role(self, role_name, department_name=None):
        """
        Check if the user has a Role with a given name and, if provided, in a specific department.
        """
        qs = self.roles.filter(name=role_name)
        if department_name:
            qs = qs.filter(department__name__iexact=department_name)
        return qs.exists()

    def in_department(self, department_name):
        """
        Check if the user has any role within the given department.
        """
        return self.roles.filter(department__name__iexact=department_name).exists()


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user')
    date_of_birth = models.DateField(null=True, blank=True)
    ghana_card_number = models.CharField(max_length=250, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='user_profile/images', null=True, blank=True)
    rating = models.PositiveIntegerField(null=True, blank=True)


@receiver(m2m_changed, sender=CustomUser.roles.through)
def sync_user_groups_with_roles(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Whenever the 'roles' ManyToMany relationship changes for a CustomUser,
    add/remove the user to/from the corresponding Django Groups.
    """
    # 'instance' is the CustomUser.
    # 'pk_set' are the primary keys of Role objects being added/removed.

    if action == 'post_add':
        # Roles have been added to this user
        for role_pk in pk_set:
            try:
                role = Role.objects.get(pk=role_pk)
                if role.group:
                    instance.groups.add(role.group)  # Add user to the group
            except Role.DoesNotExist:
                pass

    elif action == 'post_remove':
        # Roles have been removed from this user
        for role_pk in pk_set:
            try:
                role = Role.objects.get(pk=role_pk)
                if role.group:
                    instance.groups.remove(role.group)  # Remove user from the group
            except Role.DoesNotExist:
                pass


class EmailVerificationCode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        # Code valid for 30 minutes for example
        return timezone.now() > (self.created_at + timedelta(minutes=30))


class PasswordResetCode(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f'PasswordResetCode for {self.user.email} - {self.code}'

    @property
    def is_expired(self):
        expiration_time = self.created_at + timezone.timedelta(minutes=10)
        return timezone.now() > expiration_time


class SiteConfiguration(models.Model):
    ...


class PendingProfileChange(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    new_email = models.EmailField(null=True, blank=True)
    new_first_name = models.CharField(max_length=100, null=True, blank=True)
    new_last_name = models.CharField(max_length=100, null=True, blank=True)
    new_phone = models.PositiveIntegerField(null=True, blank=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_expired(self):
        # Code valid for 10 minutes
        return timezone.now() > (self.created_at + timezone.timedelta(minutes=10))

    def __str__(self):
        return f'Pending changes for {self.user.email}'





