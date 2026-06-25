"""Authentication endpoints (JWT).

These subclass Simple JWT's generic views so the routes are owned by this app
and remain a natural place to customise the request/response contract later
(e.g. returning user details alongside the tokens). Both views are public --
Simple JWT applies ``AllowAny`` regardless of the project-wide default of
``IsAuthenticated``.
"""
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class LoginView(TokenObtainPairView):
    """Authenticate with username + password; returns an access/refresh pair."""


class TokenRefreshAPIView(TokenRefreshView):
    """Exchange a valid refresh token for a new access token."""
