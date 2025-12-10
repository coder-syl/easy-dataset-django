"""
检查更新URL配置
"""
from django.urls import path
from . import views

app_name = 'utils_check_update'

urlpatterns = [
    path('', views.check_update, name='check_update'),  # GET: 检查更新
]

