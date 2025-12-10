"""
文本分割URL配置（用于split路由）
"""
from django.urls import path
from . import views

app_name = 'split'

urlpatterns = [
    path('', views.chunk_list_split, name='list_split'),  # GET: 获取列表, POST: 分割文本
]

