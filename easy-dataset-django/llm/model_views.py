"""
LLM 模型管理视图占位
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from projects.models import Project
from llm.models import LlmModel, ModelConfig, LlmProvider
from common.response.result import success, error
import requests


@swagger_auto_schema(method='get', operation_summary='获取模型列表')
@swagger_auto_schema(method='post', operation_summary='同步模型列表')
@api_view(['GET', 'POST'])
def llm_model_list(request):
    """全局模型列表/同步"""
    if request.method == 'GET':
        # 仅返回在 ModelConfig 中且已配置 api_key 的模型
        configs = ModelConfig.objects.exclude(api_key='').all()
        data = [
            {
                'id': str(c.id),
                'modelId': c.model_id,
                'modelName': c.model_name,
                'providerId': c.provider_id,
                'endpoint': c.endpoint,
                'apiKeyConfigured': bool(c.api_key)
            }
            for c in configs
        ]
        return success(data=data)
    else:
        body = request.data
        new_models = body.get('newModels', [])
        provider_id = body.get('providerId')
        if not provider_id:
            return error(message='providerId不能为空', response_status=status.HTTP_400_BAD_REQUEST)
        provider, _ = LlmProvider.objects.get_or_create(id=provider_id, defaults={
            'name': provider_id,
            'api_url': ''
        })
        created = 0
        for item in new_models:
            mid = item.get('modelId')
            mname = item.get('modelName', mid)
            if not mid:
                continue
            if not LlmModel.objects.filter(model_id=mid, provider=provider).exists():
                LlmModel.objects.create(
                    model_id=mid,
                    model_name=mname,
                    provider=provider
                )
                created += 1
        return success(data={'created': created})


@swagger_auto_schema(method='get', operation_summary='获取Ollama模型列表')
@api_view(['GET'])
def ollama_models(request):
    """Ollama 模型列表，尝试调用本地/自定义endpoint的 /api/tags"""
    endpoint = request.GET.get('endpoint') or 'http://127.0.0.1:11434'
    try:
        resp = requests.get(f"{endpoint.rstrip('/')}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        models = []
        for item in data.get('models', []):
            mid = item.get('name')
            if mid:
                models.append({'modelId': mid, 'modelName': mid, 'providerId': 'ollama'})
        return success(data=models)
    except Exception as e:
        return error(message=f'获取Ollama模型失败: {e}', response_status=status.HTTP_502_BAD_GATEWAY)


@swagger_auto_schema(method='get', operation_summary='获取项目模型列表')
@swagger_auto_schema(method='put', operation_summary='更新项目模型列表')
@api_view(['GET', 'PUT'])
def project_models(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'GET':
        # Return global model configs (ModelConfig no longer bound to Project)
        configs = ModelConfig.objects.exclude(api_key='')
        data = [{'id': str(c.id), 'modelId': c.model_id, 'modelName': c.model_name, 'providerId': c.provider_id} for c in configs]
        return success(data=data)
    else:
        # 简单覆盖更新：接受configs数组
        configs = request.data.get('configs', [])
        # Create any provided configs as global entries if they don't already exist
        created = 0
        for cfg in configs:
            provider_id = cfg.get('providerId', '')
            model_id = cfg.get('modelId', '')
            if not provider_id or not model_id:
                continue
            exists = ModelConfig.objects.filter(provider_id=provider_id, model_id=model_id).exists()
            if exists:
                continue
            ModelConfig.objects.create(
                provider_id=provider_id,
                provider_name=cfg.get('providerName', ''),
                endpoint=cfg.get('endpoint', ''),
                api_key=cfg.get('apiKey', ''),
                model_id=model_id,
                model_name=cfg.get('modelName', ''),
                type=cfg.get('type', 'text'),
                temperature=cfg.get('temperature', 0.7),
                max_tokens=cfg.get('maxTokens', 8192),
                top_p=cfg.get('topP', 1.0),
                top_k=cfg.get('topK', 0),
                status=cfg.get('status', 1)
            )
            created += 1
        return success(data={'updated': True, 'count': created})


@swagger_auto_schema(method='get', operation_summary='获取项目模型详情')
@swagger_auto_schema(method='put', operation_summary='更新项目模型详情')
@api_view(['GET', 'PUT'])
def project_model_detail(request, project_id, model_id):
    project = get_object_or_404(Project, id=project_id)
    try:
        # ModelConfig is global; just fetch by id
        config = ModelConfig.objects.get(id=model_id)
    except ModelConfig.DoesNotExist:
        return error(message='模型不存在', response_status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        data = {
            'id': str(config.id),
            'modelId': config.model_id,
            'modelName': config.model_name,
            'providerId': config.provider_id,
            'endpoint': config.endpoint
        }
        return success(data=data)
    else:
        for field in ['provider_id', 'provider_name', 'endpoint', 'api_key', 'model_id', 'model_name', 'type', 'temperature', 'max_tokens', 'top_p', 'top_k', 'status']:
            if field in request.data:
                setattr(config, field, request.data.get(field))
        config.save()
        return success(data={'updated': True})

