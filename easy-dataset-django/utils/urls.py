"""
工具类URL配置
"""
from django.urls import path
from . import views

app_name = 'utils'

# 为不同的路由创建不同的URL配置
fetch_models_urlpatterns = [
    path('', views.fetch_models, name='fetch_models'),  # POST: 获取模型列表
]

check_update_urlpatterns = [
    path('', views.check_update, name='check_update'),  # GET: 检查更新
]

update_urlpatterns = [
    path('', views.execute_update, name='execute_update'),  # POST: 执行更新
]
