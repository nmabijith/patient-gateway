"""Authentication endpoints (JWT)."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .auth_biz import store_tokens_for_user


class LoginView(TokenObtainPairView):
    """Authenticate with username + password and return an access/refresh pair.

    The issued tokens are also stored in Redis (keyed by user). Public endpoint:
    Simple JWT applies AllowAny regardless of the project-wide default.
    """

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store_tokens_for_user(serializer.user, serializer.validated_data)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
