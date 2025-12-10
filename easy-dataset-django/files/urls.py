"""
文件URL配置
"""
from django.urls import path
from . import views
from . import preview_views
from . import ga_views

app_name = 'files'

urlpatterns = [
    path('', views.file_list_upload_delete, name='list_upload_delete'),  # GET/POST/DELETE
    path('preview/<str:file_id>/', preview_views.file_preview, name='preview'),  # GET: 预览文件
    path('<str:file_id>/ga-pairs/', ga_views.generate_ga_for_file, name='ga_pairs'),  # POST: 单文件GA对
]
