"""
LLM URL配置
"""
from django.urls import path
from . import views
from . import model_views
from . import playground_views

app_name = 'llm'

urlpatterns = [
    path('providers/', views.provider_list, name='providers'),  # GET: 获取提供商列表
    path('model/', model_views.llm_model_list, name='model_list'),  # GET/POST: 模型列表/同步
    path('ollama/models/', model_views.ollama_models, name='ollama_models'),  # GET: Ollama模型列表
    path('projects/<str:project_id>/models/', model_views.project_models, name='project_models'),  # GET/PUT
    path('projects/<str:project_id>/models/<str:model_id>/', model_views.project_model_detail, name='project_model_detail'),  # GET/PUT
    # 全局模型配置（不再绑定到项目）
    path('model-config/', views.model_config_list_create, name='model_config_list_create'),  # GET/POST
    path('model-config/<str:model_config_id>/', views.model_config_detail_update_delete, name='model_config_detail'),  # GET/PUT/DELETE
    path('model-config/custom-prompts/', views.custom_prompt_list_create_delete, name='custom_prompt_list_create_delete'),
    # Playground 全局接口（不绑定项目）
    path('playground/chat/', playground_views.playground_chat_global, name='playground_chat_global'),
    path('playground/chat/stream/', playground_views.playground_chat_stream_global, name='playground_chat_stream_global'),
]
