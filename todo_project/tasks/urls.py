# tasks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("rag/upload/", views.rag_upload, name="rag_upload"),
    path("rag/chat/", views.rag_chat, name="rag_chat"),
    path("rag/query/", views.rag_query, name="rag_query"),
]
