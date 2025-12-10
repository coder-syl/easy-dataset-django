"""
LLaMA Factory 配置检查视图占位
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from projects.models import Project
from common.response.result import success, error


@swagger_auto_schema(
    method='post',
    operation_summary='检查LLaMA Factory配置',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'formatType': openapi.Schema(type=openapi.TYPE_STRING),
            'systemPrompt': openapi.Schema(type=openapi.TYPE_STRING),
            'confirmedOnly': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'includeCOT': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'reasoningLanguage': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('检查结果')}
)
@api_view(['POST'])
def llama_factory_check_config(request, project_id):
    """检查LLaMA Factory配置：检测导出文件是否存在"""
    try:
        _ = get_object_or_404(Project, id=project_id)
        from pathlib import Path
        project_path = Path('local-db') / project_id
        config_path = project_path / 'dataset_info.json'
        exists = config_path.exists()
        return success(data={
            'exists': exists,
            'configPath': str(config_path) if exists else None
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

