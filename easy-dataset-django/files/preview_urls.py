"""
文件预览URL配置（与 Node.js 路径一致）
"""
from django.urls import path
from . import preview_views

app_name = 'preview'

urlpatterns = [
    path('', preview_views.file_preview, name='preview'),  # GET: 预览文件
]

