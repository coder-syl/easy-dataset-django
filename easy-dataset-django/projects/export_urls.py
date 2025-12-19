"""
项目导出URL配置
"""
from django.urls import path
from . import export_views
from . import llamafactory_views

app_name = 'projects_export'

urlpatterns = [
    path('huggingface/upload/', export_views.huggingface_upload, name='huggingface_upload'),  # POST: 上传到HuggingFace
    path('checkConfig/', llamafactory_views.llama_factory_check_config, name='llama_factory_check'),  # GET: 检查配置
    path('generate/', export_views.llama_factory_generate, name='llama_factory_generate'),  # POST: 生成配置
]

