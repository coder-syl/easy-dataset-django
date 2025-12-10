"""
项目配置视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from pathlib import Path
import json

from .models import Project
from common.response.result import success, error


@swagger_auto_schema(
    method='get',
    operation_summary='获取项目配置',
    responses={200: openapi.Response('项目配置')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新项目配置',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'prompts': openapi.Schema(type=openapi.TYPE_OBJECT)
        }
    ),
    responses={200: openapi.Response('更新成功')}
)
@api_view(['GET', 'PUT'])
def project_config(request, project_id):
    """获取或更新项目配置"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            # 获取任务配置
            project_root = Path('local-db') / project_id
            task_config_path = project_root / 'task-config.json'
            
            task_config = {}
            if task_config_path.exists():
                with open(task_config_path, 'r', encoding='utf-8') as f:
                    task_config = json.load(f)
            
            # 返回项目信息和配置
            config = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'globalPrompt': project.global_prompt,
                'questionPrompt': project.question_prompt,
                'answerPrompt': project.answer_prompt,
                'labelPrompt': project.label_prompt,
                'domainTreePrompt': project.domain_tree_prompt,
                'cleanPrompt': project.clean_prompt,
                'defaultModelConfigId': project.default_model_config_id,
                **task_config
            }
            
            return success(data=config)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            new_config = request.data
            prompts = new_config.get('prompts', {})
            
            # 更新项目提示词
            if prompts:
                project.global_prompt = prompts.get('globalPrompt', project.global_prompt)
                project.question_prompt = prompts.get('questionPrompt', project.question_prompt)
                project.answer_prompt = prompts.get('answerPrompt', project.answer_prompt)
                project.label_prompt = prompts.get('labelPrompt', project.label_prompt)
                project.domain_tree_prompt = prompts.get('domainTreePrompt', project.domain_tree_prompt)
                project.clean_prompt = prompts.get('cleanPrompt', project.clean_prompt)
                project.save()
            
            return success(data={
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'globalPrompt': project.global_prompt,
                'questionPrompt': project.question_prompt,
                'answerPrompt': project.answer_prompt,
                'labelPrompt': project.label_prompt,
                'domainTreePrompt': project.domain_tree_prompt,
                'cleanPrompt': project.clean_prompt
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

