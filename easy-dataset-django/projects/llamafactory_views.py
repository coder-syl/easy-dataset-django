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
    method='get',
    operation_summary='检查LLaMA Factory配置',
    responses={200: openapi.Response('检查结果')}
)
@api_view(['GET'])
def llama_factory_check_config(request, project_id):
    """检查LLaMA Factory配置：检测导出文件是否存在"""
    try:
        _ = get_object_or_404(Project, id=project_id)
        from pathlib import Path
        project_path = Path('local-db') / project_id
        # 支持按数据集类型保存配置（例如 'single' / 'multi' / 'image'）
        dataset_type = request.GET.get('datasetType') or None
        if not dataset_type:
            dataset_type = 'single'
        project_subpath = project_path / dataset_type
        config_path = project_subpath / 'dataset_info.json'
        exists = config_path.exists()
        files = []
        if exists:
            # 检查常见的导出文件是否存在并列出（位于类型子目录下）
            candidates = [
                ('dataset_info.json', 'config'),
                ('alpaca.json', 'alpaca'),
                ('sharegpt.json', 'sharegpt'),
                ('multilingual-thinking.json', 'multilingual-thinking')
            ]
            for fname, fmt in candidates:
                p = project_subpath / fname
                if p.exists():
                    files.append({'path': str(p), 'format': fmt})

        return success(data={
            'exists': exists,
            'configPath': str(config_path) if exists else None,
            'files': files
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

