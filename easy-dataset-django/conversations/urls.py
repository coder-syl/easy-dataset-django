"""
多轮对话URL配置
"""
from django.urls import path
from . import views

app_name = 'conversations'

urlpatterns = [
    path('', views.conversation_list_create, name='list_create'),  # GET/POST
    path('export/', views.export_conversations, name='export'),  # GET: 导出
    path('<str:conversation_id>/', views.conversation_detail_update_delete, name='detail_update_delete'),  # GET/PUT/DELETE
]

