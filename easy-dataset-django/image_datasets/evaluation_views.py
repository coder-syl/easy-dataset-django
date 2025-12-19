"""
图像数据集评估视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
import json
import logging

from projects.models import Project
from .models import ImageDataset
from common.response.result import success, error
from common.services.llm_service import LLMService
from common.services.prompt_service import get_dataset_evaluation_prompt

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    operation_summary='评估图像数据集',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('评估结果')}
)
@api_view(['POST'])
def evaluate_image_dataset(request, project_id, dataset_id):
    """评估单个图像数据集"""
    from .services import evaluate_image_dataset_service
    
    model = request.data.get('model')
    language = request.data.get('language', 'zh-CN')
    
    if not model:
        return error(message='Model cannot be empty', response_status=status.HTTP_400_BAD_REQUEST)
    
    result = evaluate_image_dataset_service(project_id, dataset_id, model, language)
    
    if not result.get('success'):
        return error(
            message=result.get('error', '评估失败'),
            response_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # 返回格式与Node.js版本一致：{success: true, message: '...', data: {...}}
    from django.http import JsonResponse
    return JsonResponse({
        'success': True,
        'message': '图像数据集评估完成',
        'data': {
            'score': result.get('score'),
            'aiEvaluation': result.get('evaluation')
        }
    })


@swagger_auto_schema(
    method='post',
    operation_summary='批量评估图像数据集',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('任务ID')}
)
@api_view(['POST'])
def batch_evaluate_image_datasets(request, project_id):
    """批量评估图像数据集"""
    from tasks.models import Task
    from tasks.task_handlers import process_image_dataset_evaluation_task
    
    model = request.data.get('model')
    language = request.data.get('language', 'zh-CN')
    
    if not model:
        return error(message='Model cannot be empty', response_status=status.HTTP_400_BAD_REQUEST)
    
    try:
        project = get_object_or_404(Project, id=project_id)
        
        # 创建后台任务
        task = Task.objects.create(
            project=project,
            task_type='image-dataset-evaluation',
            status='pending',
            config=json.dumps({
                'model': model,
                'language': language
            })
        )
        
        # 异步处理任务（使用 Celery）
        from tasks.celery_tasks import process_task_async
        process_task_async.delay(task.id)
        
        return success(data={'taskId': task.id})
    except Exception as e:
        logger.error(f'批量评估图像数据集失败: {str(e)}', exc_info=True)
        return error(message=f'批量评估失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

