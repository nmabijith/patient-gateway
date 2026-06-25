from django.urls import path

from .views import LoginView, TokenRefreshAPIView

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', TokenRefreshAPIView.as_view(), name='auth-token-refresh'),
]
