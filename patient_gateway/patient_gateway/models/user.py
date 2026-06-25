
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Application user. Authenticates with username + password and is issued
    JWT access/refresh tokens by the auth endpoints."""

    class Meta:
        app_label = 'api'
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.get_username()
