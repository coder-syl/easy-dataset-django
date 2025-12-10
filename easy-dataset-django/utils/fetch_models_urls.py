"""
获取模型列表URL配置
"""
from django.urls import path
from . import views

app_name = 'utils_fetch_models'

urlpatterns = [
    path('', views.fetch_models, name='fetch_models'),  # POST: 获取模型列表
]

