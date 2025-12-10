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
            'gaPairId': openapi.Schema(type=openapi.TYPE_STRING)
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
    try:
        project = get_object_or_404(Project, id=project_id)
        chunk = get_object_or_404(Chunk, id=chunk_id, project=project)
    except Exception as e:
        return error(message='文本块不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'POST':
        try:
            from questions.services import generate_questions_for_chunk
            
            model = request.data.get('model')
            language = request.data.get('language', '中文')
            count = request.data.get('count', 5)
            ga_pair_id = request.data.get('gaPairId')
            
            if not model:
                return error(message='模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            result = generate_questions_for_chunk(project_id, chunk_id, {
                'model': model,
                'language': language,
                'count': count,
                'gaPairId': ga_pair_id
            })
            
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

