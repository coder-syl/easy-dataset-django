"""
文本块URL配置
"""
from django.urls import path
from . import views
from . import advanced_views
from . import name_views
from . import question_views  # 导入 question_views 以使用支持 GA 扩展的 chunk_questions

app_name = 'chunks'

urlpatterns = [
    path('', views.chunk_list_split, name='list_split'),  # GET: 获取列表, POST: 分割文本
    # 批量操作路由必须在动态路由之前，避免被 <str:chunk_id> 匹配
    path('batch-edit/', advanced_views.batch_edit_chunks, name='batch_edit'),  # POST: 批量编辑
    path('batch-delete/', advanced_views.batch_delete_chunks, name='batch_delete'),  # DELETE: 批量删除
    path('batch-content/', advanced_views.batch_content_chunks, name='batch_content'),  # POST: 批量获取内容
    path('name/', name_views.chunk_update_name, name='update_name'),  # PUT: 批量更新名称
    # 动态路由放在最后
    path('<str:chunk_id>/', views.chunk_detail_update_delete, name='detail_update_delete'),  # GET/PUT/DELETE
    path('<str:chunk_id>/questions/', question_views.chunk_questions, name='chunk_questions'),  # GET/POST: 文本块问题（使用支持 GA 扩展的版本）
    path('<str:chunk_id>/clean/', advanced_views.clean_chunk, name='clean'),  # POST: 清洗文本块
]
