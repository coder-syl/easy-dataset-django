"""
项目模型配置URL（需要在项目路由中包含）

注意：由于主路由已经包含了 'model-config/'，这里使用空字符串或相对路径
主路由: api/projects/<str:project_id>/model-config/
"""
from django.urls import path
from . import views

app_name = 'llm'

urlpatterns = [
    path('', views.model_config_list_create, name='model_config_list_create'),  # GET/POST: /api/projects/<project_id>/model-config/
    path('<str:model_config_id>/', views.model_config_detail_update_delete, name='model_config_detail'),  # GET/PUT/DELETE: /api/projects/<project_id>/model-config/<model_config_id>/
    path('custom-prompts/', views.custom_prompt_list_create_delete, name='custom_prompt_list_create_delete'),  # GET/POST/DELETE: /api/projects/<project_id>/model-config/custom-prompts/
]
