from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.DATA_ENTRY_OPERATOR)
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.SUPER_ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "সুপার অ্যাডমিন"
        DATA_ENTRY_OPERATOR = "DATA_ENTRY_OPERATOR", "ডাটা এন্ট্রি অপারেটর"

    role = models.CharField(max_length=32, choices=Role.choices, default=Role.DATA_ENTRY_OPERATOR)
    phone = models.CharField(max_length=20, blank=True)

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def save(self, *args, **kwargs):
        if self.role == self.Role.SUPER_ADMIN:
            self.is_staff = True
            self.is_superuser = True
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)

    @property
    def is_super_admin(self):
        return self.is_active and self.role == self.Role.SUPER_ADMIN

    @property
    def is_operator(self):
        return self.is_active and self.role == self.Role.DATA_ENTRY_OPERATOR

    @property
    def display_name(self):
        full = self.get_full_name().strip()
        return full or self.username


class LoginAttempt(models.Model):
    username = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField()
    successful = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["username", "ip_address", "attempted_at"]),
        ]

    def __str__(self):
        return f"{self.username} @ {self.ip_address}"
