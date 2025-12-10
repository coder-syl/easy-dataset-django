"""
项目迁移相关URL
"""
from django.urls import path
from . import migrate_views

app_name = 'projects_migrate'

urlpatterns = [
    path('', migrate_views.migrate_project, name='migrate'),  # POST: 开始迁移, GET: 查询状态
]
"""
项目迁移URL配置
"""
from django.urls import path
from . import migrate_views

app_name = 'projects_migrate'

urlpatterns = [
    path('', migrate_views.unmigrated_projects, name='unmigrated'),  # GET: 获取未迁移项目
    path('', migrate_views.migrate_project, name='migrate'),  # POST/GET: 迁移项目
]
