"""
任务URL配置
"""
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_config_list_create, name='config_list_create'),  # GET/PUT/POST: 任务配置和创建
    path('list/', views.task_list, name='list'),  # GET: 获取任务列表
    path('<str:task_id>/', views.task_detail_update_delete, name='detail_update_delete'),  # GET/PUT/PATCH/DELETE
]

