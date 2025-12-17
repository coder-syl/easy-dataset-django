"""
LLM流式响应服务
支持Server-Sent Events (SSE)格式
"""
import json
import re
from typing import Iterator, Dict, List, Optional
import requests
from django.http import StreamingHttpResponse


class LLMStreamingService:
    """LLM流式响应服务"""
    
    def __init__(self, model_config: Dict):
        # 兼容驼峰/下划线
        self.provider_id = (model_config.get('providerId') or model_config.get('provider_id') or 'openai').lower()
        self.endpoint = model_config.get('endpoint', '')
        self.api_key = model_config.get('apiKey') or model_config.get('api_key') or ''
        self.model_id = model_config.get('modelId') or model_config.get('model_id') or model_config.get('modelName', '')
        self.temperature = model_config.get('temperature', 0.7)
        self.max_tokens = model_config.get('maxTokens') or model_config.get('max_tokens', 8192)
        self.top_p = model_config.get('topP') or model_config.get('top_p', 1.0)
        self.top_k = model_config.get('topK') or model_config.get('top_k', 0)
    
    def stream_chat_sse(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """
        流式生成对话响应（SSE格式）
        :param messages: 对话历史
        :param kwargs: 其他参数
        :return: SSE格式的字符串迭代器
        """
        try:
            # 根据provider选择不同的流式实现
            if self.provider_id.lower() == 'ollama':
                yield from self._stream_ollama(messages, **kwargs)
            else:
                # OpenAI兼容格式
                yield from self._stream_openai_compatible(messages, **kwargs)
        except Exception as e:
            # 发送错误信息
            error_data = json.dumps({'error': str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
            yield "data: [DONE]\n\n"
    
    def _stream_openai_compatible(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """OpenAI兼容格式的流式响应"""
        url = f"{self.endpoint.rstrip('/')}/chat/completions"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}' if self.api_key else ''
        }
        
        payload = {
            'model': self.model_id,
            'messages': messages,
            'stream': True,
            'temperature': kwargs.get('temperature', self.temperature),
            'max_tokens': kwargs.get('max_tokens', self.max_tokens),
            'top_p': kwargs.get('top_p', self.top_p)
        }
        
        if self.top_k and self.top_k > 0:
            payload['top_k'] = self.top_k
        
        try:
            response = requests.post(url, json=payload, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            buffer = ''
            is_thinking = False
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                line_text = line.decode('utf-8')
                
                # 处理SSE格式
                if line_text.startswith('data: '):
                    data_str = line_text[6:]  # 移除 'data: ' 前缀
                    
                    if data_str.strip() == '[DONE]':
                        if is_thinking:
                            yield f"data: {json.dumps({'type': 'reasoning', 'content': '</think>'}, ensure_ascii=False)}\n\n"
                        yield "data: [DONE]\n\n"
                        break
                    
                    try:
                        data = json.loads(data_str)
                        
                        # 提取内容
                        choices = data.get('choices', [])
                        if choices:
                            delta = choices[0].get('delta', {})
                            
                            # 处理思维链（reasoning_content）
                            reasoning_content = delta.get('reasoning_content') or delta.get('reasoning')
                            if reasoning_content:
                                if not is_thinking:
                                    yield f"data: {json.dumps({'type': 'reasoning', 'content': '<think>'}, ensure_ascii=False)}\n\n"
                                    is_thinking = True
                                yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_content}, ensure_ascii=False)}\n\n"
                            
                            # 处理正文内容
                            content = delta.get('content')
                            if content is not None:
                                if is_thinking:
                                    yield f"data: {json.dumps({'type': 'reasoning', 'content': '</think>'}, ensure_ascii=False)}\n\n"
                                    is_thinking = False
                                yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            error_data = json.dumps({'error': str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    def _stream_ollama(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """Ollama格式的流式响应"""
        url = f"{self.endpoint.rstrip('/')}/api/chat"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # 转换消息格式
        ollama_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                continue  # Ollama不支持system消息
            ollama_messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        payload = {
            'model': self.model_id,
            'messages': ollama_messages,
            'stream': True,
            'options': {
                'temperature': kwargs.get('temperature', self.temperature),
                'num_predict': kwargs.get('max_tokens', self.max_tokens),
                'top_p': kwargs.get('top_p', self.top_p)
            }
        }
        
        if self.top_k and self.top_k > 0:
            payload['options']['top_k'] = self.top_k
        
        try:
            response = requests.post(url, json=payload, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            is_thinking = False
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                try:
                    data = json.loads(line.decode('utf-8'))
                    
                    # 检查是否完成
                    if data.get('done', False):
                        if is_thinking:
                            yield f"data: {json.dumps({'type': 'reasoning', 'content': '</think>'}, ensure_ascii=False)}\n\n"
                        yield "data: [DONE]\n\n"
                        break
                    
                    # 处理思维链
                    thinking = data.get('message', {}).get('thinking')
                    if thinking:
                        if not is_thinking:
                            yield f"data: {json.dumps({'type': 'reasoning', 'content': '<think>'}, ensure_ascii=False)}\n\n"
                            is_thinking = True
                        yield f"data: {json.dumps({'type': 'reasoning', 'content': thinking}, ensure_ascii=False)}\n\n"
                    
                    # 处理正文内容
                    content = data.get('message', {}).get('content')
                    if content:
                        if is_thinking:
                            yield f"data: {json.dumps({'type': 'reasoning', 'content': '</think>'}, ensure_ascii=False)}\n\n"
                            is_thinking = False
                        yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            error_data = json.dumps({'error': str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"


def create_streaming_response(stream_generator: Iterator[str]) -> StreamingHttpResponse:
    """
    创建流式HTTP响应
    :param stream_generator: 字符串生成器
    :return: StreamingHttpResponse
    """
    response = StreamingHttpResponse(stream_generator, content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    # 注意：Connection 是 hop-by-hop 头，不能由应用程序设置，由服务器/代理处理
    response['X-Accel-Buffering'] = 'no'  # 禁用Nginx缓冲
    # 添加 CORS 头，支持跨域请求
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response['Access-Control-Expose-Headers'] = 'Content-Type'
    return response

