# todo_project/todo/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from tasks import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.registerPage, name='register'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('', views.index, name='index'),
    path('update_task/<str:pk>/', views.updateTask, name='update_task'),
    path('delete_task/<str:pk>/', views.deleteTask, name='delete_task'),
    path('forgot-password/', views.forgotPassword, name='forgot_password'),
    path('', include('tasks.urls')),  # include RAG URLs here
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
