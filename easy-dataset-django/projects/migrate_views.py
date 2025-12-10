"""
项目迁移视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from pathlib import Path
import os

from .models import Project
from common.response.result import success, error

# 存储迁移任务状态（内存中，生产环境应使用Redis或数据库）
migration_tasks = {}


@swagger_auto_schema(
    method='get',
    operation_summary='获取未迁移项目列表',
    responses={200: openapi.Response('未迁移项目列表')}
)
@api_view(['GET'])
def unmigrated_projects(request):
    """获取未迁移项目列表"""
    try:
        # 获取项目根目录
        project_root = Path('local-db')
        
        if not project_root.exists():
            return success(data=[])
        
        # 读取所有文件夹
        project_dirs = [d for d in project_root.iterdir() if d.is_dir()]
        
        if len(project_dirs) == 0:
            return success(data=[])
        
        # 获取所有项目ID
        project_ids = [d.name for d in project_dirs]
        
        # 查询已迁移的项目
        existing_projects = Project.objects.filter(id__in=project_ids).values_list('id', flat=True)
        existing_project_ids = set(existing_projects)
        
        # 筛选出未迁移的项目
        unmigrated_projects = [pid for pid in project_ids if pid not in existing_project_ids]
        
        return success(data={
            'data': unmigrated_projects,
            'projectRoot': str(project_root),
            'number': len(unmigrated_projects),
            'timestamp': int(os.path.getmtime(str(project_root)) if project_root.exists() else 0)
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='开始迁移任务',
    responses={200: openapi.Response('迁移任务ID')}
)
@swagger_auto_schema(
    method='get',
    operation_summary='获取迁移任务状态',
    responses={200: openapi.Response('迁移任务状态')}
)
@api_view(['POST', 'GET'])
def migrate_project(request):
    """项目迁移"""
    if request.method == 'POST':
        try:
            # 生成任务ID
            import time
            task_id = str(int(time.time() * 1000))
            
            # 初始化任务状态
            migration_tasks[task_id] = {
                'status': 'running',
                'progress': 0,
                'total': 0,
                'completed': 0,
                'error': None,
                'startTime': int(time.time() * 1000)
            }
            
            # TODO: 异步执行迁移任务
            # execute_migration_task(task_id)
            
            return success(data={'taskId': task_id})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'GET':
        try:
            task_id = request.GET.get('taskId')
            
            if not task_id:
                return error(message='缺少任务ID', response_status=status.HTTP_400_BAD_REQUEST)
            
            task = migration_tasks.get(task_id)
            
            if not task:
                return error(message='任务不存在', response_status=status.HTTP_404_NOT_FOUND)
            
            return success(data={'task': task})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
