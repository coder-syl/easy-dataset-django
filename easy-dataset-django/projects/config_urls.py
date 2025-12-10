"""
项目配置URL
"""
from django.urls import path
from . import config_views

app_name = 'projects_config'

urlpatterns = [
    path('', config_views.project_config, name='config'),
]
"""
项目配置URL配置
"""
from django.urls import path
from . import config_views

app_name = 'projects_config'

urlpatterns = [
    path('', config_views.project_config, name='config'),  # GET/PUT: 获取/更新配置
]

