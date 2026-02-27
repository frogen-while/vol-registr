from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('about/', views.about, name='about'),
    path('api/register/', views.api_register_team, name='api_register'),
]
