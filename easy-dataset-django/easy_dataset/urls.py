"""
URL configuration for easy_dataset project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Easy-Fine-Tunning API",
        default_version='v1',
        description="Easy-Fine-Tunning API Documentation",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # 将特殊路由放在通用路由之前，避免被 project_id 匹配
    path('api/projects/unmigrated/', include(('projects.migrate_urls', 'projects'), namespace='unmigrated')),
    path('api/projects/migrate/', include(('projects.migrate_urls', 'projects'), namespace='migrate')),
    path('api/projects/', include('projects.urls')),
    path('api/projects/<str:project_id>/config/', include(('projects.config_urls', 'projects'), namespace='project_config')),
    path('api/projects/<str:project_id>/files/', include('files.urls')),
    path('api/projects/<str:project_id>/preview/<str:file_id>/', include('files.preview_urls')),  # 预览文件（与 Node.js 路径一致）
    path('api/projects/<str:project_id>/huggingface/', include(('projects.export_urls', 'projects'), namespace='huggingface')),
    path('api/projects/<str:project_id>/llamaFactory/', include(('projects.export_urls', 'projects'), namespace='llamafactory')),
    path('api/projects/<str:project_id>/playground/', include('llm.playground_urls')),
    path('api/projects/<str:project_id>/split/', include(('chunks.split_urls', 'chunks'), namespace='split')),  # 文本分割
    path('api/projects/<str:project_id>/chunks/', include(('chunks.urls', 'chunks'), namespace='chunks')),
    path('api/projects/<str:project_id>/questions/', include('questions.urls')),
    path('api/projects/<str:project_id>/generate-questions/', include(('questions.generate_views', 'questions'), namespace='generate')),
    path('api/projects/<str:project_id>/tags/', include('tags.urls')),
    path('api/projects/<str:project_id>/default-prompts/', include(('prompts.urls', 'prompts'), namespace='default_prompts')),
    path('api/projects/<str:project_id>/custom-prompts/', include(('prompts.urls', 'prompts'), namespace='custom_prompts')),
    path('api/projects/<str:project_id>/datasets/', include('datasets.urls')),
    path('api/projects/<str:project_id>/dataset-conversations/', include('conversations.urls')),
    path('api/projects/<str:project_id>/tasks/', include('tasks.urls')),
    path('api/projects/<str:project_id>/images/', include('images.urls')),
    path('api/projects/<str:project_id>/image-datasets/', include('image_datasets.urls')),
    path('api/projects/<str:project_id>/distill/', include('distill.urls')),
    path('api/projects/<str:project_id>/batch-generateGA/', include(('files.batch_urls', 'files'), namespace='batch_ga')),
    path('api/projects/<str:project_id>/model-config/', include(('llm.project_urls', 'llm'), namespace='project_model_config')),
    path('api/llm/', include(('llm.urls', 'llm'), namespace='llm')),
    path('api/llm/fetch-models/', include('utils.fetch_models_urls')),
    path('api/check-update/', include('utils.check_update_urls')),
    # dataset square
    path('api/dataset_square/', include('dataset_square.urls')),
    path('api/update/', include('utils.update_urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
