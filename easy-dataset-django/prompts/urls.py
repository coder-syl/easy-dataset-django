"""
提示词URL配置
"""
from django.urls import path
from . import views

app_name = 'prompts'

urlpatterns = [
    path('default-prompts/', views.default_prompts, name='default'),
    path('custom-prompts/', views.custom_prompts, name='custom'),
]

