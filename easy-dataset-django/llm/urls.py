"""
LLM URL配置
"""
from django.urls import path
from . import views
from . import model_views

app_name = 'llm'

urlpatterns = [
    path('providers/', views.provider_list, name='providers'),  # GET: 获取提供商列表
    path('model/', model_views.llm_model_list, name='model_list'),  # GET/POST: 模型列表/同步
    path('ollama/models/', model_views.ollama_models, name='ollama_models'),  # GET: Ollama模型列表
    path('projects/<str:project_id>/models/', model_views.project_models, name='project_models'),  # GET/PUT
    path('projects/<str:project_id>/models/<str:model_id>/', model_views.project_model_detail, name='project_model_detail'),  # GET/PUT
]
