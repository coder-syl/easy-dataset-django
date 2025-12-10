"""
执行更新URL配置
"""
from django.urls import path
from . import views

app_name = 'utils_update'

urlpatterns = [
    path('', views.execute_update, name='execute_update'),  # POST: 执行更新
]

