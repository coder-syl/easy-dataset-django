"""
文本块问题生成视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from projects.models import Project
from .models import Chunk
from questions.models import Question
from questions.serializers import QuestionSerializer
from common.response.result import success, error


@swagger_auto_schema(
    method='post',
    operation_summary='为文本块生成问题',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING),
            'count': openapi.Schema(type=openapi.TYPE_INTEGER),
            'gaPairId': openapi.Schema(type=openapi.TYPE_STRING),
            'enableGaExpansion': openapi.Schema(type=openapi.TYPE_BOOLEAN)
        }
    ),
    responses={200: openapi.Response('生成成功')}
)
@swagger_auto_schema(
    method='get',
    operation_summary='获取文本块的问题列表',
    responses={200: openapi.Response('问题列表')}
)
@api_view(['POST', 'GET'])
def chunk_questions(request, project_id, chunk_id):
    """为文本块生成问题或获取问题列表"""
    import logging
    logger = logging.getLogger('chunks')
    logger.info(f'[chunk_questions] 收到请求: method={request.method}, project_id={project_id}, chunk_id={chunk_id}')
    
    try:
        project = get_object_or_404(Project, id=project_id)
        chunk = get_object_or_404(Chunk, id=chunk_id, project=project)
        logger.debug(f'[chunk_questions] 文本块存在: chunk_id={chunk_id}, file_id={chunk.file_id if hasattr(chunk, "file_id") else "None"}')
    except Exception as e:
        logger.error(f'[chunk_questions] 文本块不存在: chunk_id={chunk_id}, error={str(e)}')
        return error(message='文本块不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'POST':
        try:
            from questions.services import generate_questions_for_chunk, generate_questions_for_chunk_with_ga
            
            model = request.data.get('model')
            language = request.data.get('language', '中文')
            count = request.data.get('count', 5)
            ga_pair_id = request.data.get('gaPairId')
            enable_ga_expansion = bool(request.data.get('enableGaExpansion', False))
            
            logger.info(f'[chunk_questions] 接收问题生成请求: chunk_id={chunk_id}, enableGaExpansion={enable_ga_expansion}, count={count}, language={language}, file_id={chunk.file_id if hasattr(chunk, "file_id") else "None"}')
            logger.debug(f'[chunk_questions] 请求数据: model存在={model is not None}, enableGaExpansion={enable_ga_expansion}, request.data.keys={list(request.data.keys())}')
            
            if not model:
                return error(message='模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 根据 enableGaExpansion 参数决定使用哪个函数
            if enable_ga_expansion:
                logger.info(f'使用 GA 扩展模式生成问题')
                # 使用 GA 扩展模式：为每个激活的 GA 对生成问题
                result = generate_questions_for_chunk_with_ga(project_id, chunk_id, {
                    'model': model,
                    'language': language,
                    'number': count,
                    'count': count
                })
            else:
                logger.info(f'使用标准模式生成问题（gaPairId={ga_pair_id}）')
                # 使用标准模式：生成问题（可选指定单个 GA 对）
                result = generate_questions_for_chunk(project_id, chunk_id, {
                    'model': model,
                    'language': language,
                    'count': count,
                    'gaPairId': ga_pair_id
                })
            
            logger.info(f'问题生成完成: 实际生成 {result.get("total", 0)} 个问题, 期望 {result.get("expectedTotal", 0)} 个问题, GA扩展={result.get("gaExpansionUsed", False)}, GA对数量={result.get("gaPairsCount", 0)}')
            
            return success(data=result)
        except Exception as e:
            return error(message=f'生成问题失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'GET':
        try:
            questions = Question.objects.filter(project=project, chunk=chunk)
            serializer = QuestionSerializer(questions, many=True)
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

