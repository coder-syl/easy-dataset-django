"""
数据集评估视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
import json
import logging

from projects.models import Project
from .models import Dataset
from tasks.models import Task
from common.response.result import success, error
from common.services.llm_service import LLMService

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    operation_summary='评估数据集',
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
def evaluate_dataset(request, project_id, dataset_id):
    """评估单个数据集"""
    from .services import evaluate_dataset_service
    
    model = request.data.get('model')
    language = request.data.get('language', 'zh-CN')
    
    if not model:
        return error(message='Model cannot be empty', response_status=status.HTTP_400_BAD_REQUEST)
    
    result = evaluate_dataset_service(project_id, dataset_id, model, language)
    
    if not result.get('success'):
        return error(
            message=result.get('error', '评估失败'),
            response_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # 返回格式与Node.js版本一致：{success: true, message: '...', data: {...}}
    from django.http import JsonResponse
    return JsonResponse({
        'success': True,
        'message': '数据集评估完成',
        'data': {
            'score': result.get('score'),
            'aiEvaluation': result.get('evaluation')
        }
    })


@swagger_auto_schema(
    method='post',
    operation_summary='批量评估数据集',
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
def batch_evaluate_datasets(request, project_id):
    """批量评估数据集"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        model = request.data.get('model')
        language = request.data.get('language', 'zh-CN')
        
        if not model or not model.get('modelName'):
            return error(message='模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 创建批量评估任务
        task = Task.objects.create(
            project=project,
            task_type='dataset-evaluation',
            status=0,
            model_info=json.dumps(model),
            language=language,
            detail='',
            total_count=0,
            note='准备开始批量评估数据集质量...',
            completed_count=0
        )
        
        # 异步处理任务
        from tasks.celery_tasks import process_task_async
        process_task_async.delay(task.id)
        
        return success(data={
            'success': True,
            'message': '批量评估任务已创建',
            'data': {'taskId': task.id}
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='优化数据集',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'datasetId': openapi.Schema(type=openapi.TYPE_STRING),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'advice': openapi.Schema(type=openapi.TYPE_STRING),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('优化结果')}
)
@api_view(['POST'])
def optimize_dataset(request, project_id):
    """优化数据集答案"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        dataset_id = request.data.get('datasetId')
        model = request.data.get('model')
        advice = request.data.get('advice')
        language = request.data.get('language', 'zh-CN')
        
        if not dataset_id:
            return error(message='Dataset ID cannot be empty', response_status=status.HTTP_400_BAD_REQUEST)
        
        if not model:
            return error(message='Model cannot be empty', response_status=status.HTTP_400_BAD_REQUEST)
        
        if not advice:
            return error(message='Please provide optimization suggestions', response_status=status.HTTP_400_BAD_REQUEST)
        
        dataset = get_object_or_404(Dataset, id=dataset_id, project=project)

        llm = LLMService(model)
        prompt = f"""You are an assistant optimizing an answer for fine-tuning.
Question: {dataset.question}
Current Answer: {dataset.answer}
Advice: {advice}
Return improved answer only."""
        resp = llm.get_response_with_cot(prompt)
        improved = (resp.get('answer') or '').strip()
        cot = resp.get('cot', '')

        if improved:
            dataset.answer = improved
            dataset.cot = cot
            dataset.save(update_fields=['answer', 'cot'])

        return success(data={
            'success': True,
            'dataset': {
                'id': dataset.id,
                'question': dataset.question,
                'answer': dataset.answer,
                'cot': dataset.cot
            }
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取Token数量',
    responses={200: openapi.Response('Token数量')}
)
@api_view(['GET'])
def token_count(request, project_id, dataset_id):
    """获取数据集的Token数量"""
    try:
        project = get_object_or_404(Project, id=project_id)
        dataset = get_object_or_404(Dataset, id=dataset_id, project=project)
        
        # 简单的Token估算（实际应该调用Tokenizer）
        question_tokens = len(dataset.question.split()) * 1.3  # 粗略估算
        answer_tokens = len(dataset.answer.split()) * 1.3
        cot_tokens = len(dataset.cot.split()) * 1.3 if dataset.cot else 0
        
        total_tokens = int(question_tokens + answer_tokens + cot_tokens)
        
        return success(data={
            'questionTokens': int(question_tokens),
            'answerTokens': int(answer_tokens),
            'cotTokens': int(cot_tokens),
            'totalTokens': total_tokens
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
