from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Add simple role choices: customer, contractor, support, admin
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('contractor', 'Contractor'),
        ('support', 'Support'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    email = models.EmailField('email address', unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
