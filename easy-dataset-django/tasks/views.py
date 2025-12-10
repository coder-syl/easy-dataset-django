"""
任务管理视图
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
import json
from pathlib import Path

from projects.models import Project
from .models import Task
from .serializers import TaskSerializer, TaskCreateSerializer
from common.response.result import success, error

logger = logging.getLogger('tasks')


@swagger_auto_schema(
    method='get',
    operation_summary='获取任务配置',
    responses={200: openapi.Response('任务配置')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新任务配置',
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT),
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='创建任务',
    request_body=TaskCreateSerializer,
    responses={201: openapi.Response('创建成功')}
)
@api_view(['GET', 'PUT', 'POST'])
def task_config_list_create(request, project_id):
    """获取任务配置、更新任务配置或创建任务"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            # 获取任务配置文件
            project_root = Path('local-db') / project_id
            task_config_path = project_root / 'task-config.json'
            
            if task_config_path.exists():
                with open(task_config_path, 'r', encoding='utf-8') as f:
                    task_config = json.load(f)
                return success(data=task_config)
            else:
                return success(data={})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            task_config = request.data
            
            # 保存任务配置文件
            project_root = Path('local-db') / project_id
            project_root.mkdir(parents=True, exist_ok=True)
            task_config_path = project_root / 'task-config.json'
            
            with open(task_config_path, 'w', encoding='utf-8') as f:
                json.dump(task_config, f, ensure_ascii=False, indent=2)
            
            return success(data={'message': '任务配置更新成功'})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            task_type = request.data.get('taskType') or request.data.get('task_type')
            logger.info(f'[{project_id}] 创建任务请求: taskType={task_type}')
            
            serializer = TaskCreateSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f'[{project_id}] 任务创建参数验证失败: {serializer.errors}')
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            # 设置项目ID
            serializer.validated_data['project'] = project
            serializer.validated_data['status'] = 0  # 初始状态: 处理中
            serializer.validated_data['completed_count'] = 0
            
            # 处理model_info和note字段（JSON字符串）
            if 'model_info' in serializer.validated_data:
                if isinstance(serializer.validated_data['model_info'], dict):
                    serializer.validated_data['model_info'] = json.dumps(serializer.validated_data['model_info'])
                elif isinstance(serializer.validated_data['model_info'], str):
                    # 如果已经是字符串，验证是否为有效JSON
                    try:
                        json.loads(serializer.validated_data['model_info'])
                    except json.JSONDecodeError:
                        logger.warning(f'[{project_id}] model_info 不是有效的JSON字符串，尝试解析')
            
            # 对于文件处理任务，验证和规范化 fileList
            if task_type == 'file-processing':
                note_data = serializer.validated_data.get('note') or {}
                if isinstance(note_data, str):
                    try:
                        note_data = json.loads(note_data)
                    except json.JSONDecodeError:
                        logger.warning(f'[{project_id}] note 不是有效的JSON字符串')
                        note_data = {}
                
                file_list_raw = note_data.get('fileList') or note_data.get('file_list') or []
                
                # 规范化 fileList：确保是文件名数组
                file_list = []
                for item in file_list_raw:
                    if isinstance(item, dict):
                        # 从对象中提取文件名
                        file_name = item.get('fileName') or item.get('file_name') or item.get('name')
                        if file_name:
                            file_list.append(file_name)
                    elif isinstance(item, str):
                        # 直接是字符串（文件名）
                        if item:
                            file_list.append(item)
                
                # 验证规范化后的 fileList 不能为空
                if not file_list or len(file_list) == 0:
                    logger.error(f'[{project_id}] 文件处理任务的 fileList 规范化后为空，原始数据: {file_list_raw}')
                    return error(
                        message='文件列表不能为空，请确保至少选择一个有效的文件',
                        response_status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 更新 note 中的 fileList
                note_data['fileList'] = file_list
                serializer.validated_data['note'] = json.dumps(note_data, ensure_ascii=False)
                
                # 设置 totalCount
                total_count = len(file_list)
                serializer.validated_data['total_count'] = total_count
                
                # 设置 detail 为 JSON 格式
                detail_data = {
                    'stepInfo': f'开始处理 {total_count} 个文件',
                    'processedFiles': 0,
                    'totalFiles': total_count,
                    'current': {'fileName': '', 'processedPage': 0, 'totalPage': 0},
                    'finishedList': [],
                    'errorList': []
                }
                serializer.validated_data['detail'] = json.dumps(detail_data, ensure_ascii=False)
                
                logger.info(f'[{project_id}] 文件处理任务, fileList数量: {total_count}, fileList: {file_list}')
                
                if total_count == 0:
                    logger.warning(f'[{project_id}] 文件处理任务的 fileList 为空，任务可能无法正常处理')
            else:
                # 非文件处理任务，正常处理 note
                if 'note' in serializer.validated_data and serializer.validated_data['note']:
                    if isinstance(serializer.validated_data['note'], dict):
                        serializer.validated_data['note'] = json.dumps(serializer.validated_data['note'], ensure_ascii=False)
                        logger.debug(f'[{project_id}] note 字段已转换为JSON字符串')
            
            task = serializer.save()
            logger.info(f'[{project_id}] 任务创建成功: taskId={task.id}, taskType={task.task_type}')
            
            # 异步启动任务处理
            from .celery_tasks import process_task_async
            process_task_async.delay(task.id)
            logger.info(f'[{project_id}] 任务已提交到异步队列: taskId={task.id}')
            
            result_serializer = TaskSerializer(task)
            return success(data=result_serializer.data, response_status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f'[{project_id}] 任务创建失败: {str(e)}', exc_info=True)
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取任务列表',
    responses={200: openapi.Response('任务列表')}
)
@api_view(['GET'])
def task_list(request, project_id):
    """获取任务列表（分页）"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        status_filter = request.GET.get('status')
        task_type_filter = request.GET.get('taskType') or request.GET.get('task_type')
        
        logger.debug(f'[{project_id}] 获取任务列表: page={page}, pageSize={page_size}, status={status_filter}, taskType={task_type_filter}')
        
        queryset = Task.objects.filter(project=project)
        
        # 状态过滤
        if status_filter is not None and status_filter != '':
            try:
                status_value = int(status_filter)
                queryset = queryset.filter(status=status_value)
            except ValueError:
                logger.warning(f'[{project_id}] 无效的状态值: {status_filter}')
        
        # 任务类型过滤
        if task_type_filter:
            queryset = queryset.filter(task_type=task_type_filter)
        
        # 按创建时间倒序，最新的任务排在最前（次级按start_time倒序）
        queryset = queryset.order_by('-create_at', '-start_time')
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = TaskSerializer(page_obj.object_list, many=True)
        logger.info(f'[{project_id}] 获取任务列表成功: 总数={paginator.count}, 当前页={page}, 返回 {len(serializer.data)} 个任务')
        
        return success(data={
            'data': serializer.data,
            'total': paginator.count,
            'page': page,
            'pageSize': page_size
        })
    except Exception as e:
        logger.error(f'[{project_id}] 获取任务列表失败: {str(e)}', exc_info=True)
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取任务详情',
    responses={200: openapi.Response('任务详情')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新任务',
    request_body=TaskSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='patch',
    operation_summary='部分更新任务',
    request_body=TaskSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除任务',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def task_detail_update_delete(request, project_id, task_id):
    """获取、更新或删除任务"""
    try:
        project = get_object_or_404(Project, id=project_id)
        task = get_object_or_404(Task, id=task_id, project=project)
    except Exception as e:
        return error(message='任务不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            serializer = TaskSerializer(task)
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method in ['PUT', 'PATCH']:
        try:
            serializer = TaskSerializer(task, data=request.data, partial=True)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            task.delete()
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
