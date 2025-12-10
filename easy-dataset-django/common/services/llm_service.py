"""
LLM服务
集成apps中的模型提供商
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Iterator
import json

# 添加apps路径
apps_path = Path(__file__).parent.parent.parent.parent / 'apps'
if str(apps_path) not in sys.path:
    sys.path.insert(0, str(apps_path))

try:
    from setting.models_provider.base_model_provider import IModelProvider, MaxKBBaseModel
    from setting.models_provider.impl.openai_model_provider.openai_model_provider import OpenAIModelProvider
    from setting.models_provider.impl.zhipu_model_provider.zhipu_model_provider import ZhipuModelProvider
    from setting.models_provider.impl.ollama_model_provider.ollama_model_provider import OllamaModelProvider
except ImportError:
    # 如果导入失败，使用简化版本
    OpenAIModelProvider = None
    ZhipuModelProvider = None
    OllamaModelProvider = None


class LLMService:
    """LLM服务类，统一调用各种模型提供商"""
    
    def __init__(self, model_config: Dict):
        """
        初始化LLM服务
        :param model_config: 模型配置字典，包含provider_id, endpoint, api_key, model_id等
        """
        # 兼容前端驼峰字段
        self.provider_id = (model_config.get('provider_id') or model_config.get('providerId') or '').lower()
        self.endpoint = model_config.get('endpoint', '')
        self.api_key = model_config.get('api_key') or model_config.get('apiKey') or ''
        self.model_id = model_config.get('model_id') or model_config.get('modelId') or ''
        self.model_name = model_config.get('model_name') or model_config.get('modelName') or ''
        self.temperature = model_config.get('temperature', 0.7)
        self.max_tokens = model_config.get('max_tokens') or model_config.get('maxTokens') or 8192
        self.top_p = model_config.get('top_p') or model_config.get('topP') or 0.9
        self.top_k = model_config.get('top_k') or model_config.get('topK') or 0
        
        self.provider = self._create_provider()
    
    def _create_provider(self):
        """创建模型提供商实例"""
        if OpenAIModelProvider is None:
            # 使用简化版本，直接调用HTTP API
            return None
        
        model_credential = {
            'api_key': self.api_key,
            'base_url': self.endpoint
        }
        
        model_params = {
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'top_p': self.top_p
        }
        
        if self.provider_id == 'openai':
            provider = OpenAIModelProvider()
        elif self.provider_id == 'zhipu':
            provider = ZhipuModelProvider()
        elif self.provider_id == 'ollama':
            provider = OllamaModelProvider()
        else:
            # 默认使用OpenAI
            provider = OpenAIModelProvider()
        
        return provider
    
    def chat(self, messages: List[Dict], **kwargs) -> Dict:
        """
        生成对话响应
        :param messages: 消息列表
        :param kwargs: 其他参数
        :return: 响应结果
        """
        if self.provider is None:
            # 使用HTTP API直接调用
            return self._call_http_api(messages, **kwargs)
        
        try:
            model = self.provider.get_model(
                'LLM',
                self.model_id,
                {'api_key': self.api_key, 'base_url': self.endpoint},
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p
            )
            
            # 调用模型
            response = model.chat(messages, **kwargs)
            return response
        except Exception as e:
            # 如果失败，回退到HTTP API
            return self._call_http_api(messages, **kwargs)
    
    def _call_http_api(self, messages: List[Dict], **kwargs) -> Dict:
        """使用HTTP API直接调用（简化版本）"""
        import requests
        
        # 根据provider_id构建API URL
        if self.provider_id == 'ollama':
            url = f"{self.endpoint.rstrip('/')}/api/chat"
        elif self.provider_id == 'zhipu':
            url = f"{self.endpoint.rstrip('/')}/chat/completions"
        else:
            # OpenAI兼容格式
            url = f"{self.endpoint.rstrip('/')}/chat/completions"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            if self.provider_id == 'zhipu':
                headers['Authorization'] = f'Bearer {self.api_key}'
            else:
                headers['Authorization'] = f'Bearer {self.api_key}'
        
        payload = {
            'model': self.model_id or self.model_name,
            'messages': messages,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'top_p': self.top_p
        }
        
        if self.top_k and self.top_k > 0:
            payload['top_k'] = self.top_k
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # 提取响应内容
        if 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0].get('message', {}).get('content', '')
            return {'answer': content, 'cot': ''}
        elif 'data' in data:
            content = data['data'].get('choices', [{}])[0].get('message', {}).get('content', '')
            return {'answer': content, 'cot': ''}
        else:
            return {'answer': str(data), 'cot': ''}
    
    def get_response_with_cot(self, prompt: str) -> Dict:
        """
        获取带思维链的响应
        :param prompt: 提示词
        :return: 包含answer和cot的字典
        """
        messages = [{'role': 'user', 'content': prompt}]
        response = self.chat(messages)
        
        # 尝试提取思维链
        answer = response.get('answer', '')
        cot = response.get('cot', '')
        
        # 如果响应中包含<think>标签，提取思维链
        if '<think>' in answer or '<think>' in answer:
            import re
            think_match = re.search(r'<think>(.*?)</think>', answer, re.DOTALL)
            if think_match:
                cot = think_match.group(1)
                answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
            
            reasoning_match = re.search(r'<think>(.*?)</think>', answer, re.DOTALL)
            if reasoning_match:
                cot = reasoning_match.group(1)
                answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
        
        return {'answer': answer.strip(), 'cot': cot.strip()}
    
    def stream_chat(self, messages: List[Dict], **kwargs) -> Iterator[Dict]:
        """
        流式生成对话响应
        :param messages: 消息列表
        :param kwargs: 其他参数
        :return: 响应字典迭代器
        """
        # 如果模型实例支持流式，优先使用
        if self.model_instance and hasattr(self.model_instance, 'stream'):
            try:
                from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
                langchain_messages = []
                for msg in messages:
                    if msg['role'] == 'user':
                        langchain_messages.append(HumanMessage(content=msg['content']))
                    elif msg['role'] == 'assistant':
                        langchain_messages.append(AIMessage(content=msg['content']))
                    elif msg['role'] == 'system':
                        langchain_messages.append(SystemMessage(content=msg['content']))
                
                merged_kwargs = {
                    'temperature': self.temperature,
                    'max_tokens': self.max_tokens,
                    'top_p': self.top_p,
                    'top_k': self.top_k,
                    **kwargs
                }
                
                for chunk in self.model_instance.stream(langchain_messages, **merged_kwargs):
                    content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                    yield {'answer': content, 'cot': ''}
            except Exception as e:
                # 如果流式失败，回退到HTTP API
                yield from self._stream_http_api(messages, **kwargs)
        else:
            # 使用HTTP API流式调用
            yield from self._stream_http_api(messages, **kwargs)
    
    def _stream_http_api(self, messages: List[Dict], **kwargs) -> Iterator[Dict]:
        """使用HTTP API进行流式调用"""
        import requests
        
        # 根据provider_id构建API URL
        if self.provider_id == 'ollama':
            url = f"{self.endpoint.rstrip('/')}/api/chat"
        elif self.provider_id == 'zhipu':
            url = f"{self.endpoint.rstrip('/')}/chat/completions"
        else:
            # OpenAI兼容格式
            url = f"{self.endpoint.rstrip('/')}/chat/completions"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        payload = {
            'model': self.model_id or self.model_name,
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
            full_answer = ''
            full_cot = ''
            is_thinking = False
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                line_text = line.decode('utf-8')
                
                # 处理SSE格式
                if line_text.startswith('data: '):
                    data_str = line_text[6:]
                    
                    if data_str.strip() == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        
                        # OpenAI格式
                        if 'choices' in data:
                            choices = data.get('choices', [])
                            if choices:
                                delta = choices[0].get('delta', {})
                                
                                # 处理思维链
                                reasoning = delta.get('reasoning_content') or delta.get('reasoning')
                                if reasoning:
                                    if not is_thinking:
                                        full_cot += '<think>'
                                        is_thinking = True
                                    full_cot += reasoning
                                
                                # 处理正文
                                content = delta.get('content')
                                if content:
                                    if is_thinking:
                                        full_cot += '</think>'
                                        is_thinking = False
                                    full_answer += content
                                    yield {'answer': content, 'cot': ''}
                        
                        # Ollama格式
                        elif 'message' in data:
                            message = data.get('message', {})
                            
                            if data.get('done', False):
                                break
                            
                            thinking = message.get('thinking')
                            if thinking:
                                if not is_thinking:
                                    full_cot += '<think>'
                                    is_thinking = True
                                full_cot += thinking
                                yield {'answer': '', 'cot': thinking}
                            
                            content = message.get('content')
                            if content:
                                if is_thinking:
                                    full_cot += '</think>'
                                    is_thinking = False
                                full_answer += content
                                yield {'answer': content, 'cot': ''}
                    except json.JSONDecodeError:
                        continue
            
            # 返回最终结果
            if full_cot:
                yield {'answer': full_answer, 'cot': full_cot}
        except Exception as e:
            yield {'answer': '', 'cot': '', 'error': str(e)}

