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
import csv
import io

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
            question_id = request.GET.get('questionId')
            role_a = request.GET.get('roleA')
            role_b = request.GET.get('roleB')
            scenario = request.GET.get('scenario')
            score_min = request.GET.get('scoreMin')
            score_max = request.GET.get('scoreMax')
            confirmed = request.GET.get('confirmed')
            
            queryset = DatasetConversation.objects.filter(project=project)
            
            if keyword:
                queryset = queryset.filter(question__icontains=keyword)
            if question_id:
                queryset = queryset.filter(question_id=question_id)
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
        # request params
        conversation_ids = request.data.get('conversationIds', [])
        export_format = request.data.get('format', 'json')  # json/jsonl/csv
        output_style = request.data.get('formatType', 'sharegpt')  # sharegpt/chatml/alpaca/raw
        confirmed_only = request.data.get('confirmedOnly', False)

        if conversation_ids:
            conversations = DatasetConversation.objects.filter(id__in=conversation_ids, project=project)
        else:
            conversations = DatasetConversation.objects.filter(project=project)

        if confirmed_only:
            conversations = conversations.filter(confirmed=True)

        payload = []
        for conv in conversations:
            # raw_messages expected to be a JSON string list of {role, content}
            try:
                messages = json.loads(conv.raw_messages)
            except Exception:
                messages = []
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
                'messages': messages
            })

        # helper to map roles to user/assistant when possible
        def map_role(msg_role, conv_item):
            try:
                if conv_item.get('roleA') and msg_role == conv_item.get('roleA'):
                    return 'user'
                if conv_item.get('roleB') and msg_role == conv_item.get('roleB'):
                    return 'assistant'
            except Exception:
                pass
            lower = (msg_role or '').lower()
            if 'user' in lower:
                return 'user'
            if 'assistant' in lower:
                return 'assistant'
            return msg_role

        exported_items = []
        if output_style == 'sharegpt':
            # ShareGPT-like export: conversations array with {from, value} entries
            for item in payload:
                conv_msgs = []
                for m in item.get('messages', []):
                    role = map_role(m.get('role'), item)
                    from_field = 'system' if role == 'system' else ('user' if 'user' in (role or '').lower() else ('assistant' if 'assistant' in (role or '').lower() else role))
                    conv_msgs.append({'from': from_field, 'value': m.get('content')})
                exported_items.append({
                    'id': item.get('id'),
                    'conversations': conv_msgs,
                    'meta': {
                        'questionId': item.get('questionId'),
                        'question': item.get('question'),
                        'model': item.get('model'),
                        'scenario': item.get('scenario'),
                        'tags': item.get('tags'),
                        'score': item.get('score'),
                        'confirmed': item.get('confirmed')
                    }
                })
        elif output_style == 'chatml':
            # For chatml, keep exported_items as normalized messages for later text rendering
            for item in payload:
                msgs = []
                for m in item.get('messages', []):
                    role = map_role(m.get('role'), item)
                    msgs.append({'role': role, 'content': m.get('content')})
                exported_items.append({
                    'id': item.get('id'),
                    'messages': msgs,
                    'meta': {
                        'questionId': item.get('questionId'),
                        'question': item.get('question'),
                        'model': item.get('model'),
                        'scenario': item.get('scenario'),
                        'tags': item.get('tags'),
                        'score': item.get('score'),
                        'confirmed': item.get('confirmed')
                    }
                })
        elif output_style == 'raw':
            # Raw: return messages as-is but normalized
            for item in payload:
                msgs = []
                for m in item.get('messages', []):
                    role = map_role(m.get('role'), item)
                    msgs.append({'role': role, 'content': m.get('content')})
                exported_items.append({
                    'id': item.get('id'),
                    'messages': msgs,
                    'meta': {
                        'questionId': item.get('questionId'),
                        'question': item.get('question'),
                        'model': item.get('model'),
                        'scenario': item.get('scenario'),
                        'tags': item.get('tags'),
                        'score': item.get('score'),
                        'confirmed': item.get('confirmed')
                    }
                })
        elif output_style == 'alpaca':
            for item in payload:
                msgs = item.get('messages', []) or []
                # normalize roles using map_role
                norm_msgs = []
                for m in msgs:
                    try:
                        role = map_role(m.get('role'), item)
                    except Exception:
                        role = (m.get('role') or '')
                    norm_msgs.append({'role': role, 'content': m.get('content')})

                # try strict user->assistant pairing first
                item_pairs = []
                for i in range(1, len(norm_msgs)):
                    prev = norm_msgs[i-1]
                    cur = norm_msgs[i]
                    prev_role = (prev.get('role') or '').lower()
                    cur_role = (cur.get('role') or '').lower()
                    if 'user' in prev_role and 'assistant' in cur_role:
                        item_pairs.append((prev, cur))

                # fallback: if no strict pairs found, pair adjacent messages
                if not item_pairs and len(norm_msgs) >= 2:
                    for i in range(1, len(norm_msgs)):
                        prev = norm_msgs[i-1]
                        cur = norm_msgs[i]
                        # prefer pairs where roles differ, otherwise still accept adjacent
                        if prev.get('content') or cur.get('content'):
                            item_pairs.append((prev, cur))

                # if only one message, export as instruction with empty output
                if not item_pairs and len(norm_msgs) == 1:
                    single = norm_msgs[0]
                    exported_items.append({
                        'instruction': single.get('content') or '',
                        'input': '',
                        'output': '',
                        'meta': {'conversationId': item.get('id')}
                    })
                else:
                    for prev, cur in item_pairs:
                        exported_items.append({
                            'instruction': prev.get('content') or '',
                            'input': '',
                            'output': cur.get('content') or '',
                            'meta': {'conversationId': item.get('id')}
                        })
        else:
            exported_items = payload

        # Special ChatML rendering if requested
        if output_style == 'chatml':
            # Build canonical ChatML blocks using <|im_start|><role> ... <|im_end|>
            chatml_blocks = []
            for it in exported_items:
                parts = []
                parts.append(f'### Conversation {it.get("id")}')
                for m in it.get('messages', []):
                    role = (m.get('role') or 'user')
                    role_token = 'system' if role and 'system' in role.lower() else ('user' if 'user' in role.lower() else ('assistant' if 'assistant' in role.lower() else role))
                    content = m.get('content', '') or ''
                    # Use canonical ChatML markers
                    parts.append(f'<|im_start|>{role_token}\n{content}\n<|im_end|>')
                chatml_blocks.append('\n'.join(parts))
            if export_format == 'jsonl':
                text = '\n'.join(json.dumps({'chatml': blk}, ensure_ascii=False) for blk in chatml_blocks)
            else:
                text = '\n\n'.join(chatml_blocks)

        # render according to export_format
        if export_format == 'jsonl':
            lines = [json.dumps(it, ensure_ascii=False) for it in exported_items]
            text = '\n'.join(lines)
        elif export_format == 'csv':
            output = io.StringIO()
            if not exported_items:
                text = ''
            else:
                first = exported_items[0]
                if isinstance(first, dict) and 'meta' in first:
                    headers = [k for k in first.keys() if k != 'meta'] + list(first['meta'].keys())
                else:
                    headers = list(first.keys())
                writer = csv.DictWriter(output, fieldnames=headers)
                writer.writeheader()
                for it in exported_items:
                    row = {}
                    for h in headers:
                        if h in it:
                            val = it[h]
                        elif isinstance(it.get('meta'), dict) and h in it.get('meta', {}):
                            val = it['meta'][h]
                        else:
                            val = ''
                        if isinstance(val, (list, dict)):
                            val = json.dumps(val, ensure_ascii=False)
                        row[h] = val
                    writer.writerow(row)
                text = output.getvalue()
        else:
            text = json.dumps(exported_items, ensure_ascii=False, indent=2)

        return success(data={
            'success': True,
            'format': export_format,
            'formatType': output_style,
            'count': len(exported_items),
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
