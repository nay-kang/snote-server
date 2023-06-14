from django.urls import path
from core.views import NoteView,ClientView
from django.http.response import HttpResponse

urlpatterns = [
    path('note/',NoteView.as_view()),
    path('note/<str:pk>',NoteView.as_view()),
    path('client/',ClientView.as_view()),
    path('client/<str:pk>',ClientView.as_view()),
]
