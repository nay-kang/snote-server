from django.urls import path
from core.views import NoteView,ClientView,EmailOTPView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenObtainPairView
)

urlpatterns = [
    path('note/',NoteView.as_view()),
    path('note/<str:pk>',NoteView.as_view()),
    path('client/',ClientView.as_view()),
    path('client/<str:pk>',ClientView.as_view()),
    path('auth/email_otp/',EmailOTPView.as_view()),
    path('auth/token/',TokenObtainPairView.as_view()),
    path('auth/token/refresh/',TokenRefreshView.as_view()),
]
