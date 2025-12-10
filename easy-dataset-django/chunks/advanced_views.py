"""
文本块高级功能视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.db.models import Q

from projects.models import Project
from .models import Chunk
from questions.models import Question
from common.response.result import success, error


@swagger_auto_schema(
    method='delete',
    operation_summary='批量删除文本块',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'chunkIds': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description='文本块ID列表'
            )
        },
        required=['chunkIds']
    ),
    responses={200: openapi.Response('删除成功')}
)
@api_view(['DELETE'])
def batch_delete_chunks(request, project_id):
    """批量删除文本块"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    try:
        # 获取文本块ID列表
        chunk_ids = request.data.get('chunkIds', [])
        
        if not chunk_ids or not isinstance(chunk_ids, list) or len(chunk_ids) == 0:
            return error(message='文本块ID列表不能为空', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 验证所有文本块都属于该项目
        chunks = Chunk.objects.filter(id__in=chunk_ids, project=project)
        found_count = chunks.count()
        
        if found_count == 0:
            return error(message='文本块不存在', response_status=status.HTTP_404_NOT_FOUND)
        
        if found_count != len(chunk_ids):
            # 部分文本块不存在或不属于该项目
            found_ids = set(chunks.values_list('id', flat=True))
            missing_ids = [cid for cid in chunk_ids if cid not in found_ids]
            return error(
                message=f'部分文本块不存在或不属于该项目: {missing_ids}',
                response_status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取所有关联的问题ID
        question_ids = list(Question.objects.filter(chunk_id__in=chunk_ids).values_list('id', flat=True))
        
        # 使用事务批量删除（按照外键依赖关系从外到内删除）
        from django.db import transaction
        
        with transaction.atomic():
            # 先删除问题（虽然设置了 CASCADE，但为了统计和明确性，显式删除）
            if question_ids:
                Question.objects.filter(id__in=question_ids).delete()
            
            # 然后删除文本块
            deleted_count = chunks.delete()[0]
        
        return success(data={
            'success': True,
            'message': f'成功删除 {deleted_count} 个文本块',
            'deletedCount': deleted_count,
            'deletedQuestionsCount': len(question_ids)
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='批量编辑文本块',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'position': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'end']),
            'content': openapi.Schema(type=openapi.TYPE_STRING),
            'chunkIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
        }
    ),
    responses={200: openapi.Response('批量编辑成功')}
)
@api_view(['POST'])
def batch_edit_chunks(request, project_id):
    """批量编辑文本块"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        position = request.data.get('position')
        content = request.data.get('content')
        chunk_ids = request.data.get('chunkIds', [])
        
        if not position or not content or not chunk_ids:
            return error(message='Missing required parameters: position, content, chunkIds', response_status=status.HTTP_400_BAD_REQUEST)
        
        if position not in ['start', 'end']:
            return error(message='Position must be "start" or "end"', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 验证文本块
        chunks = Chunk.objects.filter(id__in=chunk_ids, project=project)
        
        if chunks.count() == 0:
            return error(message='Not found', response_status=status.HTTP_404_NOT_FOUND)
        
        if chunks.count() != len(chunk_ids):
            return error(message='Some chunks not found', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 批量更新
        updated_count = 0
        for chunk in chunks:
            if position == 'start':
                chunk.content = content + '\n\n' + chunk.content
            else:
                chunk.content = chunk.content + '\n\n' + content
            chunk.size = len(chunk.content)
            chunk.save()
            updated_count += 1
        
        return success(data={
            'success': True,
            'updatedCount': updated_count,
            'message': f'Successfully updated {updated_count} chunks'
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='批量获取文本块内容',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'chunkNames': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
        }
    ),
    responses={200: openapi.Response('文本块内容映射')}
)
@api_view(['POST'])
def batch_content_chunks(request, project_id):
    """批量获取文本块内容"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        chunk_names = request.data.get('chunkNames', [])
        
        if not isinstance(chunk_names, list):
            return error(message='chunkNames 参数必须是数组', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 获取文本块内容
        chunks = Chunk.objects.filter(project=project, name__in=chunk_names)
        
        chunk_content_map = {chunk.name: chunk.content for chunk in chunks}
        
        return success(data=chunk_content_map)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='清洗文本块',
    responses={200: openapi.Response('清洗成功')}
)
@api_view(['POST'])
def clean_chunk(request, project_id, chunk_id):
    """清洗文本块"""
    try:
        project = get_object_or_404(Project, id=project_id)
        chunk = get_object_or_404(Chunk, id=chunk_id, project=project)

        model_config = request.data.get('model')
        language = request.data.get('language', '中文')

        if not model_config:
            return error(message='模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)

        from .services import clean_chunk_content
        result = clean_chunk_content(project_id, chunk_id, model_config, language)

        return success(data={
            'success': True,
            'chunkId': result['chunkId'],
            'cleanedLength': result['cleanedLength'],
            'content': result['content']
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取文本块的问题',
    responses={200: openapi.Response('问题列表')}
)
@api_view(['GET'])
def chunk_questions(request, project_id, chunk_id):
    """获取文本块的问题"""
    try:
        project = get_object_or_404(Project, id=project_id)
        chunk = get_object_or_404(Chunk, id=chunk_id, project=project)
        
        questions = Question.objects.filter(chunk=chunk, project=project)
        
        questions_data = [{
            'id': q.id,
            'question': q.question,
            'label': q.label,
            'answered': q.answered
        } for q in questions]
        
        return success(data=questions_data)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='put',
    operation_summary='更新文本块名称',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('更新成功')}
)
@api_view(['PUT'])
def update_chunk_name(request, project_id):
    """更新文本块名称"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        chunk_id = request.data.get('chunkId')
        name = request.data.get('name')
        
        if not chunk_id or not name:
            return error(message='chunkId and name are required', response_status=status.HTTP_400_BAD_REQUEST)
        
        chunk = get_object_or_404(Chunk, id=chunk_id, project=project)
        chunk.name = name
        chunk.save()
        
        return success(data={
            'id': chunk.id,
            'name': chunk.name
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
