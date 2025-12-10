"""
文本块管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator

from projects.models import Project
from .models import Chunk
from .serializers import ChunkSerializer
from tags.models import Tag
from questions.models import Question
from questions.serializers import QuestionSerializer
from common.response.result import success, error


@swagger_auto_schema(
    method='get',
    operation_summary='获取文本块列表',
    responses={200: openapi.Response('文本块列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='分割文本',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'fileNames': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('分割成功')}
)
@api_view(['GET', 'POST'])
def chunk_list_split(request, project_id):
    """获取文本块列表或分割文本"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            # 获取查询参数
            filter_type = request.GET.get('filter', '')
            
            # 构建查询
            queryset = Chunk.objects.filter(project=project).exclude(
                name__in=['Image Chunk', 'Distilled Content']
            )
            
            # 过滤条件
            if filter_type == 'generated':
                queryset = queryset.filter(questions__isnull=False).distinct()
            elif filter_type == 'ungenerated':
                queryset = queryset.filter(questions__isnull=True)
            
            # 获取标签
            tags = Tag.objects.filter(project=project)
            tags_data = [{'id': tag.id, 'label': tag.label, 'parentId': tag.parent_id} for tag in tags]
            
            # 获取文本块和文件结果
            from .services import get_project_chunks
            chunks_result = get_project_chunks(project_id, filter_type)
            
            # 与 Node.js GET 接口返回格式保持一致
            # Node.js 返回: { chunks, ...result.fileResult, tags }
            # 其中 result.fileResult 包含 { fileName, totalChunks, chunks, toc }
            # 展开后 toc 在顶层
            file_result = chunks_result.get('fileResult', {})
            
            return success(data={
                'chunks': chunks_result.get('chunks', []),
                'fileName': file_result.get('fileName', ''),
                'totalChunks': file_result.get('totalChunks', 0),
                'toc': file_result.get('toc', ''),  # toc 在顶层，与 Node.js 一致
                'tags': tags_data
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            # 文本分割功能
            file_names = request.data.get('fileNames', [])
            model = request.data.get('model')
            language = request.data.get('language', 'zh-CN')
            domain_tree_action = request.data.get('domainTreeAction', 'rebuild')
            
            if not model:
                return error(message='请选择模型', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 集成文本分割逻辑
            from .services import split_project_file
            
            result = {
                'totalChunks': 0,
                'chunks': [],
                'toc': ''
            }
            
            for file_name in file_names:
                try:
                    split_result = split_project_file(project_id, file_name)
                    result['toc'] += split_result.get('toc', '') + '\n'
                    result['chunks'].extend(split_result.get('chunks', []))
                    result['totalChunks'] += split_result.get('totalChunks', 0)
                except Exception as e:
                    return error(message=f'分割文件 {file_name} 失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 获取标签
            tags = Tag.objects.filter(project=project)
            tags_data = [{'id': tag.id, 'label': tag.label, 'parentId': tag.parent_id} for tag in tags]
            
            return success(data={
                **result,
                'tags': tags_data
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取文本块详情',
    responses={200: openapi.Response('文本块详情')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新文本块',
    request_body=ChunkSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='patch',
    operation_summary='部分更新文本块',
    request_body=ChunkSerializer,
    responses={200: openapi.Response('部分更新成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除文本块',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def chunk_detail_update_delete(request, project_id, chunk_id):
    """获取、更新或删除文本块"""
    try:
        project = get_object_or_404(Project, id=project_id)
        chunk = get_object_or_404(Chunk, id=chunk_id, project=project)
    except Exception as e:
        return error(message='文本块不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            serializer = ChunkSerializer(chunk)
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            serializer = ChunkSerializer(chunk, data=request.data, partial=True)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'PATCH':
        try:
            serializer = ChunkSerializer(chunk, data=request.data, partial=True)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            chunk.delete()
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
