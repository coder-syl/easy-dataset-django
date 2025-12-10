"""
问题批量生成视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.urls import path

from projects.models import Project
from chunks.models import Chunk
from common.response.result import success, error
from .services import generate_questions_for_chunk_with_ga, generate_questions_for_chunk


@swagger_auto_schema(
    method='post',
    operation_summary='批量生成问题',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'chunkIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'language': openapi.Schema(type=openapi.TYPE_STRING),
            'enableGaExpansion': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        }
    ),
    responses={200: openapi.Response('生成结果')}
)
@api_view(['POST'])
def generate_questions(request, project_id):
    """
    按项目批量生成问题（可选指定chunkIds）
    """
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)

    try:
        model = request.data.get('model')
        chunk_ids = request.data.get('chunkIds', [])
        language = request.data.get('language', '中文')
        enable_ga_expansion = bool(request.data.get('enableGaExpansion', False))

        if not model:
            return error(message='模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)

        # 如果未指定 chunkIds，取该项目全部 chunk
        if not chunk_ids:
            chunk_ids = list(Chunk.objects.filter(project=project).values_list('id', flat=True))

        if len(chunk_ids) == 0:
            return error(message='没有可用的文本块', response_status=status.HTTP_404_NOT_FOUND)

        results = []
        errors = []

        for cid in chunk_ids:
            try:
                chunk = Chunk.objects.get(id=cid, project=project)
            except Chunk.DoesNotExist:
                errors.append({'chunkId': cid, 'error': '文本块不存在'})
                continue

            try:
                if enable_ga_expansion:
                    res = generate_questions_for_chunk_with_ga(project_id, str(chunk.id), {
                        'model': model,
                        'language': language,
                        'number': 5
                    })
                    results.append({'chunkId': str(chunk.id), 'success': True, 'data': res})
                else:
                    res = generate_questions_for_chunk(project_id, str(chunk.id), {
                        'model': model,
                        'language': language,
                        'number': 5
                    })
                    results.append({'chunkId': str(chunk.id), 'success': True, 'data': res})
            except Exception as e:
                errors.append({'chunkId': str(chunk.id), 'error': str(e)})

        return success(data={
            'results': results,
            'errors': errors,
            'total': len(chunk_ids),
            'success': len(results),
            'failed': len(errors)
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
"""
问题生成视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from pathlib import Path
import json

from projects.models import Project
from chunks.models import Chunk
from .models import Question
from common.response.result import success, error
from common.services.text_splitter import split_project_file


@swagger_auto_schema(
    method='post',
    operation_summary='批量生成问题',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'chunkIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'language': openapi.Schema(type=openapi.TYPE_STRING),
            'enableGaExpansion': openapi.Schema(type=openapi.TYPE_BOOLEAN)
        }
    ),
    responses={200: openapi.Response('生成结果')}
)
@api_view(['POST'])
def generate_questions(request, project_id):
    """批量生成问题"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        model = request.data.get('model')
        chunk_ids = request.data.get('chunkIds', [])
        language = request.data.get('language', '中文')
        enable_ga_expansion = request.data.get('enableGaExpansion', False)
        
        if not model:
            return error(message='The model cannot be empty', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 获取文本块
        if not chunk_ids or len(chunk_ids) == 0:
            # 获取所有文本块
            chunks = Chunk.objects.filter(project=project).exclude(name__in=['Image Chunk', 'Distilled Content'])
        else:
            # 获取指定的文本块
            chunks = Chunk.objects.filter(id__in=chunk_ids, project=project)
        
        if chunks.count() == 0:
            return error(message='No valid text blocks found', response_status=status.HTTP_404_NOT_FOUND)
        
        # 获取任务配置
        project_root = Path('local-db') / project_id
        task_config_path = project_root / 'task-config.json'
        question_generation_length = 500  # 默认值
        
        if task_config_path.exists():
            with open(task_config_path, 'r', encoding='utf-8') as f:
                task_config = json.load(f)
                question_generation_length = task_config.get('questionGenerationLength', 500)
        
        results = []
        errors = []
        
        from .services import generate_questions_for_chunk, generate_questions_for_chunk_with_ga
        
        for chunk in chunks:
            try:
                # 根据文本长度自动计算问题数量
                question_number = max(1, chunk.size // question_generation_length)
                
                if enable_ga_expansion:
                    result = generate_questions_for_chunk_with_ga(
                        str(project.id),
                        str(chunk.id),
                        {
                            'model': model,
                            'language': language,
                            'number': question_number
                        }
                    )
                else:
                    result = generate_questions_for_chunk(
                        str(project.id),
                        str(chunk.id),
                        {
                            'model': model,
                            'language': language,
                            'number': question_number
                        }
                    )
                
                # 统一处理返回结果格式
                if result and result.get('questions'):
                    results.append({
                        'chunkId': str(chunk.id),
                        'success': True,
                        'questions': result.get('questions', []),
                        'total': result.get('total', 0),
                        'gaExpansionUsed': result.get('gaExpansionUsed', False),
                        'gaPairsCount': result.get('gaPairsCount', 0)
                    })
                elif result and result.get('labelQuestions'):
                    results.append({
                        'chunkId': str(chunk.id),
                        'success': True,
                        'questions': result.get('labelQuestions', []),
                        'total': result.get('total', 0),
                        'gaExpansionUsed': False,
                        'gaPairsCount': 0
                    })
                else:
                    errors.append({
                        'chunkId': str(chunk.id),
                        'error': 'Failed to parse questions'
                    })
            except Exception as e:
                errors.append({
                    'chunkId': str(chunk.id),
                    'error': str(e)
                })
        
        return success(data={
            'results': results,
            'errors': errors,
            'totalSuccess': len(results),
            'totalErrors': len(errors),
            'totalChunks': chunks.count()
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


urlpatterns = [
    path('', generate_questions, name='generate_questions'),
]
