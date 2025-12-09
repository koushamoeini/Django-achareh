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

    def __str__(self):
        return f"{self.username} ({self.role})"
