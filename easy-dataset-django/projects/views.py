"""
项目管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from .models import Project
from .serializers import ProjectSerializer, ProjectCreateSerializer
from llm.models import ModelConfig
from common.response.result import success, error


@swagger_auto_schema(
    method='get',
    operation_summary='获取项目列表',
    responses={200: openapi.Response('项目列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='创建项目',
    request_body=ProjectCreateSerializer,
    responses={201: openapi.Response('创建成功')}
)
@api_view(['GET', 'POST'])
def project_list_create(request):
    """获取项目列表或创建项目"""
    if request.method == 'GET':
        try:
            # 使用 prefetch_related 优化查询，避免 N+1 问题
            projects = Project.objects.prefetch_related('questions', 'datasets').all().order_by('-create_at')
            serializer = ProjectSerializer(projects, many=True)
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            serializer = ProjectCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            # 验证项目名称是否已存在
            name = serializer.validated_data.get('name')
            if Project.objects.filter(name=name).exists():
                return error(message='项目名称已存在', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 创建项目
            project = serializer.save()
            
            # 如果指定了要复用的项目配置
            reuse_config_from = request.data.get('reuseConfigFrom')
            if reuse_config_from:
                try:
                    source_configs = ModelConfig.objects.filter(project_id=reuse_config_from)
                    new_configs = []
                    for config in source_configs:
                        new_config = ModelConfig(
                            project=project,
                            provider_id=config.provider_id,
                            provider_name=config.provider_name,
                            endpoint=config.endpoint,
                            api_key=config.api_key,
                            model_id=config.model_id,
                            model_name=config.model_name,
                            type=config.type,
                            temperature=config.temperature,
                            max_tokens=config.max_tokens,
                            top_p=config.top_p,
                            top_k=config.top_k,
                            status=config.status
                        )
                        new_configs.append(new_config)
                    ModelConfig.objects.bulk_create(new_configs)
                except Exception as e:
                    # 配置复制失败不影响项目创建
                    pass
            
            result_serializer = ProjectSerializer(project)
            return success(data=result_serializer.data, response_status=status.HTTP_201_CREATED)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取项目详情',
    responses={200: openapi.Response('项目详情')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新项目',
    request_body=ProjectSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除项目',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'PUT', 'DELETE'])
def project_detail_update_delete(request, project_id):
    """获取、更新或删除项目"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            serializer = ProjectSerializer(project)
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            serializer = ProjectSerializer(project, data=request.data, partial=True)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            project.delete()
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
