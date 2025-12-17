"""
LLM 模型测试视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from projects.models import Project
from common.response.result import success, error
import json


@swagger_auto_schema(
    method='post',
    operation_summary='模型测试聊天',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'messages': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'temperature': openapi.Schema(type=openapi.TYPE_NUMBER),
            'maxTokens': openapi.Schema(type=openapi.TYPE_INTEGER)
        }
    ),
    responses={200: openapi.Response('聊天响应')}
)
@api_view(['POST'])
def playground_chat(request, project_id):
    """模型测试聊天"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        messages = request.data.get('messages', [])
        model = request.data.get('model')
        temperature = request.data.get('temperature', 0.7)
        max_tokens = request.data.get('maxTokens', 8192)
        
        if not messages or not model:
            return error(message='消息和模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)

        # 清洗消息：仅保留 user/assistant/system，且内容非空
        def _normalize_msg(msg):
            content = msg.get('content')
            role = msg.get('role')
            if isinstance(content, str):
                if not content.strip():
                    return None
                return {'role': role, 'content': content}
            if isinstance(content, list):
                if len(content) == 0:
                    return None
                return {'role': role, 'content': content}
            return None

        cleaned_messages = []
        for m in messages:
            if m.get('role') not in ('user', 'assistant', 'system'):
                continue
            nm = _normalize_msg(m)
            if nm:
                cleaned_messages.append(nm)

        if not cleaned_messages:
            return error(message='消息内容为空', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 集成LLM调用逻辑
        from common.services.llm_service import LLMService
        
        try:
            llm_service = LLMService(model)
            response = llm_service.chat(cleaned_messages, temperature=temperature, max_tokens=max_tokens)
            
            # 前端对齐 Node 版本接口，直接返回 { response: '...' }
            return success(data={'response': response.get('answer', '')})
        except Exception as e:
            return error(message=f'聊天失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='模型测试流式聊天',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'messages': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'temperature': openapi.Schema(type=openapi.TYPE_NUMBER),
            'maxTokens': openapi.Schema(type=openapi.TYPE_INTEGER)
        }
    ),
    responses={200: openapi.Response('流式响应')}
)
@api_view(['POST'])
def playground_chat_stream(request, project_id):
    """模型测试流式聊天（SSE格式）"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        messages = request.data.get('messages', [])
        model_config = request.data.get('model')
        temperature = request.data.get('temperature', 0.7)
        max_tokens = request.data.get('maxTokens', 8192)
        
        if not messages or not model_config:
            return error(message='消息和模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 使用流式服务
        from common.services.llm_streaming import LLMStreamingService, create_streaming_response
        
        streaming_service = LLMStreamingService(model_config)
        
        # 生成流式响应
        def stream_generator():
            try:
                for chunk in streaming_service.stream_chat_sse(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    yield chunk
            except Exception as e:
                error_data = json.dumps({'error': str(e)}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
                yield "data: [DONE]\n\n"
        
        return create_streaming_response(stream_generator())
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

