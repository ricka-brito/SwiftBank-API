"""
Models de toda a aplicação
"""

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)

from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager for users."""

    @classmethod
    def normalize_cpf(self, cpf: str):
        """Method to remove the special characters of the cpf string"""

        return cpf.replace(".", "").replace("-", "").replace("/", "")

    def create_user(self, cpf, password=None, **extra_fields):
        """Create, save and return a new user."""

        if not cpf:
            raise ValueError("User must have an cpf")

        user = self.model(cpf=self.normalize_cpf(cpf), **extra_fields)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, cpf, password):
        """Create, save and return a new super user"""

        user = self.create_user(cpf, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in system"""

    cpf = models.CharField(max_length=11, unique=True)
    first_name = models.CharField(max_length=255, null=False)
    last_name = models.CharField(max_length=255, null=False)
    email = models.EmailField(max_length=255, unique=True)
    # url_imagem = models.ImageField(null=True, upload_to=user_image_field)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'cpf'

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name}'
