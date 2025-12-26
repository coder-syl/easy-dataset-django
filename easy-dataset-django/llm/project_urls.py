"""
项目模型配置URL（需要在项目路由中包含）

注意：由于主路由已经包含了 'model-config/'，这里使用空字符串或相对路径
主路由: api/projects/<str:project_id>/model-config/
"""
from django.urls import path
from . import views

app_name = 'llm'

urlpatterns = [
    # 保留自定义提示词的项目级接口（路径仍为 /api/projects/<project_id>/model-config/custom-prompts/）
    path('custom-prompts/', views.custom_prompt_list_create_delete, name='custom_prompt_list_create_delete'),
]
