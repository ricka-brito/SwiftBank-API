"""
Models de toda a aplicação
"""
import os
from urllib import request 
import uuid 
from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

def user_image_field(instance, filename):
    """Generate file path for new user image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'
    
    return os.path.join('uploads', 'user', filename)

class LoginAttempt(models.Model):
    username = models.CharField(max_length=255)
    successful = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)
    ip = models.CharField(max_length=255)
    
    
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


class Address(models.Model):
    """Address for users"""
    street = models.CharField(max_length=255)
    neighborhood = models.CharField(max_length=255)
    house_number = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    complement  = models.CharField(max_length=255, blank=True)
    cep = models.CharField(max_length=8)
    reference = models.CharField(max_length=255, blank=True)
    uf = models.CharField(max_length=2)

    def __str__(self):
        return f'{self.street}, {self.city}'

class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""

    cpf = models.CharField(max_length=11, unique=True)
    first_name = models.CharField(max_length=255, null=False)
    email = models.EmailField(max_length=255)
    url_imagem = models.ImageField(null=True, upload_to='uploads/user/')
    phone_number = models.CharField(max_length=15)
    declared_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    addresses = models.ManyToManyField(Address, related_name='users', blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'cpf'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    
class Account(models.Model):
    """Account for every user """

    agency = models.CharField(max_length=4, default="0001")
    number = models.CharField(max_length=8)
    balance = models.DecimalField(max_digits=5, decimal_places=2)
    user = models.OneToOneField(
        User,
        on_delete=models.DO_NOTHING,
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f'{self.agency} - {self.number}'



class Transaction(models.Model):
    """Model for transaction"""
    
    class TransactionTypes(models.TextChoices):
        TRANSFER = 'TR', _('Transfer')
        WITHDRAW = 'WD', _('Withdraw')
        DEPOSIT = 'DP', _('Deposit')
        CREDIT = 'CR', _('Credit')
        LOAN = 'LN', _('Loan')
    
    sender = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="sender", null=True, blank=True)
    receiver = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="receiver", null=True, blank=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, null=True, blank=True)
    transaction_type = models.CharField(max_length=2, choices=TransactionTypes.choices)
    created_at = models.DateTimeField(default=timezone.now)


class Loan(models.Model):
    """Model for loan"""

    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    installments = models.IntegerField()
    request_date = models.DateTimeField(default=timezone.now)
    payed = models.BooleanField(default=False)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    fees = models.DecimalField(max_digits=5, decimal_places=3)

class LoanInstallments(models.Model):
    """Model of installments of a loan"""

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="installment")
    payed_date = models.DateTimeField(null=True)
    due_date = models.DateTimeField(null=False)
    value = models.DecimalField(max_digits=10,decimal_places=2)