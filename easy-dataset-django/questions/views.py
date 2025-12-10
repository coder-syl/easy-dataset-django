"""
问题管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q

from projects.models import Project
from chunks.models import Chunk
from .models import Question
from .serializers import QuestionSerializer, QuestionCreateSerializer
from common.response.result import success, error


@swagger_auto_schema(
    method='get',
    operation_summary='获取问题列表',
    responses={200: openapi.Response('问题列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='创建问题',
    request_body=QuestionCreateSerializer,
    responses={201: openapi.Response('创建成功')}
)
@api_view(['GET', 'POST'])
def question_list_create(request, project_id):
    """获取问题列表或创建问题"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            # 获取查询参数
            status_param = request.GET.get('status')
            answered = None
            if status_param == 'answered':
                answered = True
            elif status_param == 'unanswered':
                answered = False
            
            chunk_name = request.GET.get('chunkName')
            source_type = request.GET.get('sourceType', 'all')  # 'all', 'text', 'image'
            selected_all = request.GET.get('selectedAll')
            get_all = request.GET.get('all')
            search_input = request.GET.get('input')
            
            # 构建查询
            queryset = Question.objects.filter(project=project)
            
            # 过滤条件
            if answered is not None:
                queryset = queryset.filter(answered=answered)
            
            if chunk_name:
                queryset = queryset.filter(chunk__name=chunk_name)
            
            if source_type == 'text':
                queryset = queryset.filter(image_id__isnull=True)
            elif source_type == 'image':
                queryset = queryset.filter(image_id__isnull=False)
            
            if search_input:
                queryset = queryset.filter(question__icontains=search_input)
            
            # 如果只需要ID列表
            if selected_all:
                question_ids = queryset.values_list('id', flat=True)
                # 与 Node.js 保持一致：返回数组格式 [{id: '...'}, {id: '...'}]
                # Node.js 的 getQuestionsIds 返回 [{id: '...'}, {id: '...'}]
                # 前端期望 response.data 是数组，每个元素有 id 属性
                question_list = [{'id': str(qid)} for qid in question_ids]
                # 直接返回数组，不使用 success() 包装，与 Node.js 保持一致
                from rest_framework.response import Response
                return Response(question_list, status=status.HTTP_200_OK)
            
            # 如果需要所有数据
            if get_all:
                serializer = QuestionSerializer(queryset, many=True)
                return success(data=serializer.data)
            
            # 分页
            page = int(request.GET.get('page', 1))
            size = int(request.GET.get('size', 20))
            paginator = Paginator(queryset, size)
            page_obj = paginator.get_page(page)
            
            serializer = QuestionSerializer(page_obj.object_list, many=True)
            return success(data={
                'data': serializer.data,
                'total': paginator.count,
                'page': page,
                'size': size
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            serializer = QuestionCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            # 设置项目ID
            serializer.validated_data['project'] = project
            question = serializer.save()
            
            result_serializer = QuestionSerializer(question)
            return success(data=result_serializer.data, response_status=status.HTTP_201_CREATED)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取问题详情',
    responses={200: openapi.Response('问题详情')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新问题',
    request_body=QuestionSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='patch',
    operation_summary='部分更新问题',
    request_body=QuestionSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除问题',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def question_detail_update_delete(request, project_id, question_id):
    """获取、更新或删除问题"""
    try:
        project = get_object_or_404(Project, id=project_id)
        question = get_object_or_404(Question, id=question_id, project=project)
    except Exception as e:
        return error(message='问题不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            serializer = QuestionSerializer(question)
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method in ['PUT', 'PATCH']:
        try:
            serializer = QuestionSerializer(question, data=request.data, partial=True)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            question.delete()
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='delete',
    operation_summary='批量删除问题',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'questionIds': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description='问题ID列表'
            )
        },
        required=['questionIds']
    ),
    responses={200: openapi.Response('删除成功')}
)
@api_view(['DELETE'])
def question_batch_delete(request, project_id):
    """批量删除问题"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    try:
        # 获取问题ID列表
        question_ids = request.data.get('questionIds', [])
        
        if not question_ids or not isinstance(question_ids, list) or len(question_ids) == 0:
            return error(message='问题ID列表不能为空', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 验证所有问题都属于该项目
        questions = Question.objects.filter(id__in=question_ids, project=project)
        found_count = questions.count()
        
        if found_count == 0:
            return error(message='问题不存在', response_status=status.HTTP_404_NOT_FOUND)
        
        if found_count != len(question_ids):
            # 部分问题不存在或不属于该项目
            found_ids = set(questions.values_list('id', flat=True))
            missing_ids = [qid for qid in question_ids if qid not in found_ids]
            return error(
                message=f'部分问题不存在或不属于该项目: {missing_ids}',
                response_status=status.HTTP_400_BAD_REQUEST
            )
        
        # 批量删除问题（级联删除会处理关联的数据集）
        deleted_count = questions.delete()[0]
        
        return success(data={
            'success': True,
            'message': f'成功删除 {deleted_count} 个问题',
            'deletedCount': deleted_count
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)