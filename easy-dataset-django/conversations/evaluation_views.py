"""
多轮对话评估视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
import json
import logging

from projects.models import Project
from .models import DatasetConversation
from common.response.result import success, error
from common.services.llm_service import LLMService
from common.services.prompt_service import get_dataset_evaluation_prompt
from common.util.json_extract import extract_json_from_llm_output
import re
from django.http import JsonResponse

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    operation_summary='评估多轮对话',
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
def evaluate_conversation(request, project_id, conversation_id):
    """评估单个多轮对话"""
    try:
        project = get_object_or_404(Project, id=project_id)
        conv = get_object_or_404(DatasetConversation, id=conversation_id, project=project)
    except Exception as e:
        return error(message='对话不存在', response_status=status.HTTP_404_NOT_FOUND)

    model = request.data.get('model')
    language = request.data.get('language', 'zh-CN')

    if not model:
        return error(message='Model cannot be empty', response_status=status.HTTP_400_BAD_REQUEST)

    try:
        # 解析 raw_messages，构建会话文本用于评估提示词
        raw = conv.raw_messages or conv.raw_messages or '[]'
        try:
            messages = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
        except Exception:
            messages = []

        conversation_lines = []
        last_user = ''
        last_assistant = ''
        if isinstance(messages, list):
            for m in messages:
                try:
                    role = m.get('role') if isinstance(m, dict) else ''
                    content = m.get('content') if isinstance(m, dict) else str(m)
                except Exception:
                    role = ''
                    content = str(m)
                conversation_lines.append(f"{role}: {content}")
                if role and role.lower().startswith('user'):
                    last_user = content
                if role and role.lower().startswith('assistant'):
                    last_assistant = content

        conversation_text = '\n'.join(conversation_lines)

        # 构建评估提示词：传入 conversation_text 作为 chunk_content，last_user 作为 question，last_assistant 作为 answer
        prompt = get_dataset_evaluation_prompt(language, conversation_text, last_user or conv.question or '', last_assistant or '', project_id)
        llm = LLMService(model)
        # 使用带思维链的调用以兼容多种 provider
        resp = llm.get_response_with_cot(prompt)
        # 兼容 resp 为 dict 或字符串
        if isinstance(resp, dict):
            answer_text = resp.get('answer') or resp.get('text') or ''
        else:
            answer_text = str(resp)

        # 尝试从 LLM 输出中提取 JSON（稳健解析）
        parsed = extract_json_from_llm_output(answer_text)
        score = None
        evaluation = None
        if isinstance(parsed, dict):
            score = parsed.get('score')
            evaluation = parsed.get('evaluation') or parsed.get('aiEvaluation') or parsed.get('result')
        else:
            # 回退：用正则从文本中提取评分
            m = re.search(r'([0-5](?:\\.5)?)', answer_text)
            if m:
                try:
                    score = float(m.group(1))
                except Exception:
                    score = None
            evaluation = answer_text

        # 规范化评分并保存
        if score is not None:
            score = max(0.0, min(5.0, float(score)))
            score = round(score * 2) / 2
            conv.score = score
        conv.ai_evaluation = evaluation or ''
        conv.save(update_fields=['score', 'ai_evaluation'])

        return JsonResponse({
            'success': True,
            'message': '对话评估完成',
            'data': {
                'score': conv.score,
                'aiEvaluation': conv.ai_evaluation
            }
        })
    except Exception as e:
        logger.error('评估对话失败: %s', str(e), exc_info=True)
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@swagger_auto_schema(
    method='post',
    operation_summary='批量评估多轮对话',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING),
            'conversationIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
        }
    ),
    responses={200: openapi.Response('批量评估任务已创建')}
)
@api_view(['POST'])
def batch_evaluate_conversations(request, project_id):
    """批量评估多轮对话（创建异步任务）"""
    from tasks.models import Task
    model = request.data.get('model')
    language = request.data.get('language', 'zh-CN')

    if not model or not model.get('modelName'):
        return error(message='模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)

    try:
        project = get_object_or_404(Project, id=project_id)
        task = Task.objects.create(
            project=project,
            task_type='conversation-evaluation',
            status=0,
            model_info=json.dumps(model),
            language=language,
            detail='',
            total_count=0,
            note='准备开始批量评估多轮对话...',
            completed_count=0
        )

        from tasks.celery_tasks import process_task_async
        process_task_async.delay(task.id)

        return JsonResponse({
            'success': True,
            'message': '批量评估任务已创建',
            'data': {'taskId': task.id}
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


