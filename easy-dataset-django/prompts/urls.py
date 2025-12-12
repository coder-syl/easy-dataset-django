"""
提示词URL配置
"""
from django.urls import path
from . import views

app_name = 'prompts'

urlpatterns = [
    # /api/projects/<project_id>/custom-prompts/default-prompts/
    path('default-prompts/', views.default_prompts, name='default'),
    # /api/projects/<project_id>/custom-prompts/  （不再重复 custom-prompts 段）
    path('', views.custom_prompts, name='custom'),
]

