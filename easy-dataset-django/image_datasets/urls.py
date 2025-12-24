"""
图像数据集URL配置
"""
from django.urls import path
from . import views
from . import extra_views
from . import evaluation_views

app_name = 'image_datasets'

urlpatterns = [
    path('', views.image_dataset_list_create, name='list_create'),  # GET/POST
    path('batch-evaluate/', evaluation_views.batch_evaluate_image_datasets, name='batch_evaluate'),  # POST
    path('export/', extra_views.export_image_datasets, name='export'),  # POST
    path('export-zip/', extra_views.export_image_datasets_zip, name='export_zip'),  # GET
    path('tags/', extra_views.image_dataset_tags, name='tags'),  # GET
    path('<str:dataset_id>/evaluate/', evaluation_views.evaluate_image_dataset, name='evaluate'),  # POST
    path('<str:dataset_id>/regenerate/', views.regenerate_image_dataset, name='regenerate'),  # POST
    path('<str:dataset_id>/', views.image_dataset_detail_update_delete, name='detail_update_delete'),  # GET/PUT/DELETE
]

