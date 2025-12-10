"""
数据集URL配置
"""
from django.urls import path
from . import views
from . import export_views
from . import token_views

app_name = 'datasets'

urlpatterns = [
    # 先放固定路由，避免被 <str:dataset_id> 捕获
    path('', views.dataset_list_create, name='list_create'),  # GET: 获取列表, POST: 生成数据集
    path('export/', export_views.dataset_export, name='export'),  # GET/POST: 导出数据集
    path('import/', export_views.dataset_import, name='import'),  # POST: 导入数据集
    path('tags/', token_views.dataset_tags, name='tags'),  # GET: 数据集标签统计
    path('batch-evaluate/', views.dataset_batch_evaluate, name='batch_evaluate'),  # POST: 批量评估
    path('optimize/', views.dataset_optimize, name='optimize'),  # POST: 优化
    path('<str:dataset_id>/token-count/', token_views.dataset_token_count, name='token_count'),  # GET: Token统计
    path('<str:dataset_id>/evaluate/', views.dataset_evaluate, name='evaluate'),  # POST: 评估单个数据集
    path('<str:dataset_id>/', views.dataset_detail_update_delete, name='detail_update_delete'),  # GET/PUT/DELETE
]

