"""
LLM管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from projects.models import Project
from .models import LlmProvider, LlmModel, ModelConfig, CustomPrompt
from .serializers import ModelConfigSerializer, ModelConfigCreateSerializer, CustomPromptSerializer
from common.response.result import success, error

# 默认模型提供商配置（与前端 constant/model.js 保持同步）
MODEL_PROVIDERS = [
    {'id': 'ollama', 'name': 'Ollama', 'defaultEndpoint': 'http://127.0.0.1:11434/api', 'defaultModels': []},
    {'id': 'openai', 'name': 'OpenAI', 'defaultEndpoint': 'https://api.openai.com/v1/', 'defaultModels': ['gpt-4o', 'gpt-4o-mini', 'o1-mini']},
    {'id': 'siliconcloud', 'name': '硅基流动', 'defaultEndpoint': 'https://api.siliconflow.cn/v1/', 'defaultModels': [
        'deepseek-ai/DeepSeek-R1',
        'deepseek-ai/DeepSeek-V3',
        'Qwen2.5-7B-Instruct',
        'meta-llama/Llama-3.3-70B-Instruct'
    ]},
    {'id': 'deepseek', 'name': 'DeepSeek', 'defaultEndpoint': 'https://api.deepseek.com/v1/', 'defaultModels': ['deepseek-chat', 'deepseek-reasoner']},
    {'id': '302ai', 'name': '302.AI', 'defaultEndpoint': 'https://api.302.ai/v1/', 'defaultModels': ['Doubao-pro-128k', 'deepseek-r1', 'kimi-latest', 'qwen-max']},
    {'id': 'zhipu', 'name': '智谱AI', 'defaultEndpoint': 'https://open.bigmodel.cn/api/paas/v4/', 'defaultModels': ['glm-4-flash', 'glm-4-flashx', 'glm-4-plus', 'glm-4-long']},
    {'id': 'Doubao', 'name': '火山引擎', 'defaultEndpoint': 'https://ark.cn-beijing.volces.com/api/v3/', 'defaultModels': []},
    {'id': 'groq', 'name': 'Groq', 'defaultEndpoint': 'https://api.groq.com/openai', 'defaultModels': ['Gemma 7B', 'LLaMA3 8B', 'LLaMA3 70B']},
    {'id': 'grok', 'name': 'Grok', 'defaultEndpoint': 'https://api.x.ai/v1', 'defaultModels': ['Grok Beta']},
    {'id': 'OpenRouter', 'name': 'OpenRouter', 'defaultEndpoint': 'https://openrouter.ai/api/v1/', 'defaultModels': [
        'google/gemma-2-9b-it:free',
        'meta-llama/llama-3-8b-instruct:free',
        'microsoft/phi-3-mini-128k-instruct:free'
    ]},
    {'id': 'alibailian', 'name': '阿里云百炼', 'defaultEndpoint': 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'defaultModels': ['qwen-max-latest', 'qwen-max-2025-01-25']},
]

DEFAULT_MODEL_SETTINGS = {
    'temperature': 0.7,
    'maxTokens': 8192,
    'topP': 0.9
}


@swagger_auto_schema(
    method='get',
    operation_summary='获取LLM提供商列表',
    responses={200: openapi.Response('提供商列表')}
)
@api_view(['GET'])
def provider_list(request):
    """获取LLM提供商列表"""
    try:
        # 严格从 llm_providers 表中读取提供商；不会回退到内置常量
        providers = LlmProvider.objects.all()
        provider_data = [{
            'id': p.id,
            'name': p.name,
            'apiUrl': p.api_url
        } for p in providers]
        return success(data=provider_data)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取模型配置列表',
    responses={200: openapi.Response('模型配置列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='保存模型配置',
    request_body=ModelConfigCreateSerializer,
    responses={200: openapi.Response('保存成功')}
)
@api_view(['GET', 'POST'])
def model_config_list_create(request):
    """获取或保存全局模型配置（不再绑定项目）"""
    if request.method == 'GET':
        try:
            # 仅返回已配置 API Key 的模型配置（数据库只保存用户主动配置的项）
            model_configs = ModelConfig.objects.exclude(api_key='')
            serializer = ModelConfigSerializer(model_configs, many=True)
            return success(data={'data': serializer.data})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        try:
            serializer = ModelConfigCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)

            if not serializer.validated_data.get('model_id'):
                serializer.validated_data['model_id'] = serializer.validated_data.get('model_name', '')

            model_config = serializer.save()
            result_serializer = ModelConfigSerializer(model_config)
            return success(data=result_serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取模型配置详情',
    responses={200: openapi.Response('模型配置详情')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新模型配置',
    request_body=ModelConfigSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除模型配置',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'PUT', 'DELETE'])
def model_config_detail_update_delete(request, model_config_id):
    """获取、更新或删除单个全局模型配置"""
    try:
        model_config = get_object_or_404(ModelConfig, id=model_config_id)
    except Exception as e:
        return error(message='模型配置不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            serializer = ModelConfigSerializer(model_config)
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            serializer = ModelConfigSerializer(model_config, data=request.data, partial=True)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()

            # 如果更新后 api_key 被清空，则删除该配置（数据库仅保存已配置 api_key 的项）
            model_config.refresh_from_db()
            if not model_config.api_key:
                model_config.delete()
                return success(data={'deleted': True})

            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            model_config.delete()
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取自定义提示词',
    responses={200: openapi.Response('提示词列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='保存自定义提示词',
    request_body=CustomPromptSerializer,
    responses={200: openapi.Response('保存成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除自定义提示词',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'POST', 'DELETE'])
def custom_prompt_list_create_delete(request, project_id):
    """自定义提示词管理"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            prompt_type = request.GET.get('promptType')
            language = request.GET.get('language')
            
            queryset = CustomPrompt.objects.filter(project=project)
            if prompt_type:
                queryset = queryset.filter(prompt_type=prompt_type)
            if language:
                queryset = queryset.filter(language=language)
            
            serializer = CustomPromptSerializer(queryset, many=True)
            
            # TODO: 获取提示词模板
            templates = []
            
            return success(data={
                'customPrompts': serializer.data,
                'templates': templates
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            # 批量保存
            if 'prompts' in request.data and isinstance(request.data['prompts'], list):
                results = []
                for prompt_data in request.data['prompts']:
                    prompt_data['project'] = project_id
                    serializer = CustomPromptSerializer(data=prompt_data)
                    if serializer.is_valid():
                        serializer.save()
                        results.append(serializer.data)
                    else:
                        results.append({'error': serializer.errors})
                return success(data={'results': results})
            
            # 单个保存
            prompt_data = request.data.copy()
            prompt_data['project'] = project_id
            serializer = CustomPromptSerializer(data=prompt_data)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return success(data={'result': serializer.data})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            prompt_type = request.GET.get('promptType')
            prompt_key = request.GET.get('promptKey')
            language = request.GET.get('language')
            
            if not all([prompt_type, prompt_key, language]):
                return error(message='promptType, promptKey和language参数不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            CustomPrompt.objects.filter(
                project=project,
                prompt_type=prompt_type,
                prompt_key=prompt_key,
                language=language
            ).delete()
            
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
