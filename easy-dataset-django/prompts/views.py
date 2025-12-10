"""
提示词管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
import importlib
import os

from projects.models import Project
from llm.models import CustomPrompt
from common.response.result import success, error


@swagger_auto_schema(
    method='get',
    operation_summary='获取默认提示词',
    responses={200: openapi.Response('默认提示词')}
)
@api_view(['GET'])
def default_prompts(request, project_id):
    """获取默认提示词"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        prompt_type = request.GET.get('promptType')
        prompt_key = request.GET.get('promptKey')
        
        if not prompt_type or not prompt_key:
            return error(message='promptType and promptKey are required', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 动态导入提示词模块
        try:
            # 从common.services.prompt_service导入
            from common.services import prompt_service
            
            # 获取提示词常量
            prompt_content = getattr(prompt_service, prompt_key, None)
            
            if not prompt_content:
                return error(message=f'Prompt key {prompt_key} not found', response_status=status.HTTP_404_NOT_FOUND)
            
            return success(data={
                'content': prompt_content,
                'promptType': prompt_type,
                'promptKey': prompt_key
            })
        except ImportError as e:
            return error(message=f'Prompt module {prompt_type} not found: {str(e)}', response_status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取自定义提示词',
    responses={200: openapi.Response('自定义提示词列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='保存自定义提示词',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'promptType': openapi.Schema(type=openapi.TYPE_STRING),
            'promptKey': openapi.Schema(type=openapi.TYPE_STRING),
            'language': openapi.Schema(type=openapi.TYPE_STRING),
            'content': openapi.Schema(type=openapi.TYPE_STRING),
            'prompts': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING)
            )
        }
    ),
    responses={200: openapi.Response('保存成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除自定义提示词',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'POST', 'DELETE'])
def custom_prompts(request, project_id):
    """自定义提示词管理"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            prompt_type = request.GET.get('promptType')
            language = request.GET.get('language')
            
            # 获取自定义提示词
            queryset = CustomPrompt.objects.filter(project=project)
            
            if prompt_type:
                queryset = queryset.filter(prompt_type=prompt_type)
            if language:
                queryset = queryset.filter(language=language)
            
            custom_prompts_data = [{
                'id': cp.id,
                'promptType': cp.prompt_type,
                'promptKey': cp.prompt_key,
                'language': cp.language,
                'content': cp.content
            } for cp in queryset]
            
            # 获取模板列表（简化版本）
            templates = []
            
            return success(data={
                'customPrompts': custom_prompts_data,
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
                    cp, created = CustomPrompt.objects.update_or_create(
                        project=project,
                        prompt_type=prompt_data.get('promptType'),
                        prompt_key=prompt_data.get('promptKey'),
                        language=prompt_data.get('language'),
                        defaults={'content': prompt_data.get('content', '')}
                    )
                    results.append({
                        'id': cp.id,
                        'created': created
                    })
                return success(data={'results': results})
            
            # 单个保存
            prompt_type = request.data.get('promptType')
            prompt_key = request.data.get('promptKey')
            language = request.data.get('language')
            content = request.data.get('content')
            
            if not all([prompt_type, prompt_key, language, content is not None]):
                return error(message='promptType, promptKey, language and content are required', response_status=status.HTTP_400_BAD_REQUEST)
            
            cp, created = CustomPrompt.objects.update_or_create(
                project=project,
                prompt_type=prompt_type,
                prompt_key=prompt_key,
                language=language,
                defaults={'content': content}
            )
            
            return success(data={'result': {
                'id': cp.id,
                'created': created
            }})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            prompt_type = request.GET.get('promptType')
            prompt_key = request.GET.get('promptKey')
            language = request.GET.get('language')
            
            if not all([prompt_type, prompt_key, language]):
                return error(message='promptType, promptKey and language are required', response_status=status.HTTP_400_BAD_REQUEST)
            
            deleted_count, _ = CustomPrompt.objects.filter(
                project=project,
                prompt_type=prompt_type,
                prompt_key=prompt_key,
                language=language
            ).delete()
            
            return success(data={'success': deleted_count > 0})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

