"""
项目URL配置
"""
from django.urls import path
from . import views
from . import migrate_views
from . import config_views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list_create, name='list_create'),  # GET: 获取列表, POST: 创建项目
    path('<str:project_id>/', views.project_detail_update_delete, name='detail_update_delete'),  # GET/PUT/DELETE
    path('<str:project_id>/config/', config_views.project_config, name='config'),  # GET/PUT: 项目配置
]
