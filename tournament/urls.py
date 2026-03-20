from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('faq/', views.faq, name='faq'),
    path('team/<int:team_id>/', views.team_detail, name='team_detail'),
    path('api/register/', views.api_register_team, name='api_register'),
    path('api/ask/', views.api_ask_question, name='api_ask_question'),
    path('privacy-policy/', views.privacy_policy_en, name='privacy_policy_en'),
]
