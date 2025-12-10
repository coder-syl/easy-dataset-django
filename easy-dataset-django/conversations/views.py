"""
多轮对话管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
import json

from projects.models import Project
from .models import DatasetConversation
from .serializers import DatasetConversationSerializer
from common.response.result import success, error


@swagger_auto_schema(
    method='get',
    operation_summary='获取多轮对话列表',
    responses={200: openapi.Response('对话列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='创建多轮对话',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'questionId': openapi.Schema(type=openapi.TYPE_STRING),
            'systemPrompt': openapi.Schema(type=openapi.TYPE_STRING),
            'scenario': openapi.Schema(type=openapi.TYPE_STRING),
            'rounds': openapi.Schema(type=openapi.TYPE_INTEGER),
            'roleA': openapi.Schema(type=openapi.TYPE_STRING),
            'roleB': openapi.Schema(type=openapi.TYPE_STRING),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('创建成功')}
)
@api_view(['GET', 'POST'])
def conversation_list_create(request, project_id):
    """获取多轮对话列表或创建多轮对话"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            get_all_ids = request.GET.get('getAllIds') == 'true'
            
            # 筛选条件
            keyword = request.GET.get('keyword')
            role_a = request.GET.get('roleA')
            role_b = request.GET.get('roleB')
            scenario = request.GET.get('scenario')
            score_min = request.GET.get('scoreMin')
            score_max = request.GET.get('scoreMax')
            confirmed = request.GET.get('confirmed')
            
            queryset = DatasetConversation.objects.filter(project=project)
            
            if keyword:
                queryset = queryset.filter(question__icontains=keyword)
            if role_a:
                queryset = queryset.filter(role_a=role_a)
            if role_b:
                queryset = queryset.filter(role_b=role_b)
            if scenario:
                queryset = queryset.filter(scenario=scenario)
            if score_min:
                queryset = queryset.filter(score__gte=float(score_min))
            if score_max:
                queryset = queryset.filter(score__lte=float(score_max))
            if confirmed is not None:
                queryset = queryset.filter(confirmed=(confirmed.lower() == 'true'))
            
            # 如果只需要ID列表
            if get_all_ids:
                conversation_ids = queryset.values_list('id', flat=True)
                return success(data={'allConversationIds': [str(id) for id in conversation_ids]})
            
            # 分页
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('pageSize', 20))
            
            paginator = Paginator(queryset.order_by('-create_at'), page_size)
            page_obj = paginator.get_page(page)
            
            serializer = DatasetConversationSerializer(page_obj.object_list, many=True)
            return success(data={
                'success': True,
                'data': serializer.data,
                'total': paginator.count,
                'page': page,
                'pageSize': page_size
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            question_id = request.data.get('questionId')
            system_prompt = request.data.get('systemPrompt', '')
            scenario = request.data.get('scenario', '')
            rounds = request.data.get('rounds', 3)
            role_a = request.data.get('roleA', '用户')
            role_b = request.data.get('roleB', '助手')
            model = request.data.get('model')
            language = request.data.get('language', '中文')
            
            if not question_id:
                return error(message='问题ID不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            if not model or not model.get('modelName'):
                return error(message='模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 生成多轮对话
            from .services import generate_multi_turn_conversation
            
            config = {
                'systemPrompt': system_prompt,
                'scenario': scenario,
                'rounds': rounds,
                'roleA': role_a,
                'roleB': role_b,
                'model': model,
                'language': language
            }
            
            result = generate_multi_turn_conversation(str(project.id), question_id, config)
            
            if not result.get('success'):
                return error(message=result.get('error', '生成失败'), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return success(data=result.get('data'))
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取对话详情',
    responses={200: openapi.Response('对话详情')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新对话',
    request_body=DatasetConversationSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除对话',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'PUT', 'DELETE'])
def conversation_detail_update_delete(request, project_id, conversation_id):
    """获取、更新或删除对话"""
    try:
        project = get_object_or_404(Project, id=project_id)
        conversation = get_object_or_404(DatasetConversation, id=conversation_id, project=project)
    except Exception as e:
        return error(message='对话不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            serializer = DatasetConversationSerializer(conversation)
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            serializer = DatasetConversationSerializer(conversation, data=request.data, partial=True)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            conversation.delete()
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='导出多轮对话',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conversationIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'format': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('导出成功')}
)
@api_view(['POST'])
def export_conversations(request, project_id):
    """导出多轮对话"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        conversation_ids = request.data.get('conversationIds', [])
        format_type = request.data.get('format', 'json')
        
        if conversation_ids:
            conversations = DatasetConversation.objects.filter(id__in=conversation_ids, project=project)
        else:
            conversations = DatasetConversation.objects.filter(project=project)

        payload = []
        for conv in conversations:
            payload.append({
                'id': conv.id,
                'questionId': conv.question_id,
                'question': conv.question,
                'chunkId': conv.chunk_id,
                'model': conv.model,
                'scenario': conv.scenario,
                'roleA': conv.role_a,
                'roleB': conv.role_b,
                'turnCount': conv.turn_count,
                'maxTurns': conv.max_turns,
                'tags': conv.tags,
                'score': conv.score,
                'aiEvaluation': conv.ai_evaluation,
                'confirmed': conv.confirmed,
                'messages': json.loads(conv.raw_messages)
            })

        if format_type == 'jsonl':
            text = '\n'.join(json.dumps(item, ensure_ascii=False) for item in payload)
        else:
            text = json.dumps(payload, ensure_ascii=False, indent=2)

        return success(data={
            'success': True,
            'format': format_type,
            'count': len(payload),
            'content': text
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取对话标签',
    responses={200: openapi.Response('标签列表')}
)
@api_view(['GET'])
def conversation_tags(request, project_id):
    """获取对话标签"""
    try:
        project = get_object_or_404(Project, id=project_id)
        qs = DatasetConversation.objects.filter(project=project).exclude(tags='')
        tag_count = {}
        for conv in qs:
            for tag in conv.tags.split(','):
                t = tag.strip()
                if not t:
                    continue
                tag_count[t] = tag_count.get(t, 0) + 1

        tags = [{'tag': k, 'count': v} for k, v in tag_count.items()]
        return success(data={'tags': tags})
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
