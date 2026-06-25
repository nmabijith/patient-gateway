"""Business logic for authentication.

Thin helpers around Simple JWT so token issuance lives in one place and can be
reused (e.g. after user registration) rather than being tied to a single view.
"""
from rest_framework_simplejwt.tokens import RefreshToken


def issue_tokens_for_user(user):
    """Return a fresh ``{access, refresh}`` JWT pair for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
