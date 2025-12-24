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
        # 请求超时配置（秒）与重试次数
        self.request_timeout = model_config.get('request_timeout') or model_config.get('timeout') or 120
        self.max_retries = int(model_config.get('retries', 2))
    
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
            
            # 如果响应是字典，尝试提取思维链
            if isinstance(response, dict):
                from .llm_util import extract_answer_and_cot
                return extract_answer_and_cot(response)
            
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
        
        # 对于非 OpenAI 模型，尝试启用思维链支持
        # OpenAI o1 系列模型会自动返回 reasoning_content，不需要额外参数
        # Qwen 模型可能需要特殊参数来生成思维链
        if self.provider_id not in ['openai']:
            # 某些模型支持 send_reasoning 或 reasoning 参数
            payload['send_reasoning'] = True
            payload['reasoning'] = True
            
            # Qwen 模型特殊处理
            if 'qwen' in (self.model_id or self.model_name or '').lower():
                # Qwen 模型可能需要 enable_thinking 参数
                payload['enable_thinking'] = True
                # 某些 Qwen API 可能需要 thinking 参数
                payload['thinking'] = True
        
        # 输出请求参数（用于调试）
        import logging
        import json
        logger = logging.getLogger(__name__)
        logger.info('=' * 80)
        logger.info('LLM API 请求参数:')
        logger.info(f'URL: {url}')
        logger.info(f'模型: {self.model_id or self.model_name}, Provider: {self.provider_id}')
        try:
            # 隐藏敏感信息（api_key）
            log_payload = payload.copy()
            if 'messages' in log_payload:
                # 只记录消息数量，不记录完整内容（可能很长）
                log_payload['messages'] = f'[{len(log_payload["messages"])} messages, first: {log_payload["messages"][0].get("content", "")[:1100]}...]'
            logger.info(f'请求参数: {json.dumps(log_payload, ensure_ascii=False, indent=2)}')
        except Exception as e:
            logger.info(f'请求参数（无法格式化）: {payload}')
        logger.info('=' * 80)
        
        # 确保 headers 可被 latin-1 编码，避免因非 ASCII 内容导致编码错误
        safe_headers = {}
        for k, v in headers.items():
            try:
                v.encode('latin-1')
                safe_headers[k] = v
            except UnicodeEncodeError:
                # 尝试降级处理，去除无法编码字符
                safe_headers[k] = v.encode('utf-8', errors='ignore').decode('latin-1', errors='ignore')
                logger.warning(f'Header {k} 包含非 ASCII 字符，已降级处理以避免编码错误。')

        # 尝试重试请求，避免临时网络或提供商短暂不可用导致任务立即失败
        last_error = None
        for attempt in range(1, max(1, self.max_retries) + 1):
            try:
                response = requests.post(url, json=payload, headers=safe_headers, timeout=self.request_timeout)
                response.raise_for_status()
                data = response.json()
                last_error = None
                break
            except Exception as e:
                last_error = e
                logger = logging.getLogger(__name__)
                logger.warning(f'LLM HTTP call attempt {attempt} failed: {str(e)}')
                # 在最后一次重试失败后，返回错误信息作为字符串，调用方将进行后续降级处理
                if attempt < max(1, self.max_retries):
                    import time
                    time.sleep(1 * attempt)
                else:
                    # 返回错误字符串以便上层不会因为异常导致整个任务中断
                    return str(e)
        
        # 提取响应内容（支持思维链）
        from .llm_util import extract_answer_and_cot
        import logging
        import json
        logger = logging.getLogger(__name__)
        
        # 输出完整的 API 响应（用于调试）
        logger.info('=' * 80)
        logger.info('LLM API 完整响应内容:')
        logger.info(f'模型: {self.model_id or self.model_name}, Provider: {self.provider_id}')
        try:
            # 格式化输出 JSON，便于阅读
            formatted_response = json.dumps(data, ensure_ascii=False, indent=2)
            logger.info(f'响应 JSON:\n{formatted_response}')
        except Exception as e:
            logger.info(f'响应内容（无法格式化JSON）: {str(data)}')
        logger.info('=' * 80)
        
        # 构建响应对象用于统一提取
        # 优先从 response.body.choices[0].message 中提取
        response_obj = {
            'text': '',
            'answer': '',
            'reasoning': '',
            'response': {
                'body': data
            }
        }
        
        # 如果响应中有 choices，尝试提取 content 和 reasoning_content
        if 'choices' in data and len(data['choices']) > 0:
            message = data['choices'][0].get('message', {})
            # 将 content 放入 text 字段，以便 extract_answer_and_cot 可以检查标签
            response_obj['text'] = message.get('content', '') or ''
            response_obj['answer'] = message.get('content', '') or ''
            # 尝试从多个可能的字段提取思维链
            response_obj['reasoning'] = (
                message.get('reasoning_content', '') or 
                message.get('reasoning', '') or 
                message.get('thinking', '') or
                ''
            )
            
            # 记录 message 的完整内容（包括所有字段）
            logger.info(f'message 完整内容: {json.dumps(message, ensure_ascii=False, indent=2)}')
            logger.info(f'message 的所有键: {list(message.keys())}')
            
            # 检查是否有思维链相关字段
            thinking_fields = ['reasoning_content', 'reasoning', 'thinking', 'cot', 'chain_of_thought', 'thought', 'reflection']
            found_thinking_fields = [field for field in thinking_fields if field in message and message.get(field)]
            if found_thinking_fields:
                logger.info(f'发现思维链相关字段: {found_thinking_fields}')
                for field in found_thinking_fields:
                    logger.info(f'  {field}: {str(message.get(field))[:200]}...')
            else:
                logger.warning(f'未发现思维链相关字段。message 中只有: {list(message.keys())}')
            
            # 检查 choices[0] 是否有其他字段（某些 API 可能在 choices 层级返回思维链）
            choice = data['choices'][0]
            choice_keys = list(choice.keys())
            logger.info(f'choices[0] 的所有键: {choice_keys}')
            for key in choice_keys:
                if key not in ['message', 'finish_reason', 'index', 'logprobs']:
                    logger.info(f'  发现额外字段 {key}: {str(choice.get(key))[:200]}...')
            
            # 检查顶层是否有思维链相关字段
            top_level_thinking_fields = [field for field in thinking_fields if field in data and data.get(field)]
            if top_level_thinking_fields:
                logger.info(f'在响应顶层发现思维链相关字段: {top_level_thinking_fields}')
                for field in top_level_thinking_fields:
                    logger.info(f'  {field}: {str(data.get(field))[:200]}...')
        elif 'data' in data and 'choices' in data.get('data', {}):
            message = data['data'].get('choices', [{}])[0].get('message', {})
            response_obj['text'] = message.get('content', '') or ''
            response_obj['answer'] = message.get('content', '') or ''
            response_obj['reasoning'] = message.get('reasoning_content', '') or message.get('reasoning', '') or ''
            
            # 记录 message 的完整内容
            logger.info(f'message 内容: {json.dumps(message, ensure_ascii=False, indent=2)}')
        
        # 使用统一提取函数（会处理标签格式、reasoning_content 等）
        result = extract_answer_and_cot(response_obj)
        
        # 如果统一提取没有结果，尝试直接提取
        if not result.get('answer') and not result.get('cot'):
            if 'choices' in data and len(data['choices']) > 0:
                message = data['choices'][0].get('message', {})
                result['answer'] = message.get('content', '') or ''
                result['cot'] = message.get('reasoning_content', '') or message.get('reasoning', '') or ''
            elif 'data' in data:
                message = data.get('data', {}).get('choices', [{}])[0].get('message', {})
                result['answer'] = message.get('content', '') or ''
                result['cot'] = message.get('reasoning_content', '') or message.get('reasoning', '') or ''
            else:
                result['answer'] = str(data)
                logger.warning(f'无法从响应中提取内容，返回原始数据')
        
        # 记录提取结果（用于调试）
        logger.info('=' * 80)
        logger.info('思维链提取结果:')
        logger.info(f'答案长度: {len(result.get("answer", ""))}')
        logger.info(f'思维链长度: {len(result.get("cot", ""))}')
        if result.get('answer'):
            logger.info(f'答案内容（前200字符）: {result["answer"][:200]}...')
        if result.get('cot'):
            logger.info(f'思维链内容（前500字符）: {result["cot"][:500]}...')
        else:
            logger.warning('未提取到思维链！')
            logger.warning('请检查：')
            logger.warning('1. 模型是否支持思维链生成')
            logger.warning('2. API 响应中是否包含 reasoning_content、reasoning 字段')
            logger.warning('3. 响应内容中是否包含 <think> 或 <thinking> 标签')
        logger.info('=' * 80)
        
        return result
    
    def get_response(self, prompt: str) -> str:
        """
        获取响应（与 Node.js 的 getResponse 保持一致，返回字符串）
        :param prompt: 提示词
        :return: 响应字符串
        """
        messages = [{'role': 'user', 'content': prompt}]
        response = self.chat(messages)
        
        # 如果响应是字典，提取 text 或 answer 字段
        if isinstance(response, dict):
            return response.get('text', '') or response.get('answer', '') or str(response)
        
        # 如果响应是字符串，直接返回
        if isinstance(response, str):
            return response
        
        # 其他情况转换为字符串
        return str(response)
    
    def get_response_with_cot(self, prompt: str) -> Dict:
        """
        获取带思维链的响应
        支持多种思维链提取方式：
        1. reasoning 字段
        2. <think> 或 <thinking> 标签
        3. OpenAI reasoning_content 字段
        :param prompt: 提示词
        :return: 包含answer和cot的字典
        """
        from .llm_util import extract_answer_and_cot
        import logging
        logger = logging.getLogger(__name__)
        
        messages = [{'role': 'user', 'content': prompt}]
        response = self.chat(messages)
        
        # 记录原始响应（用于调试）
        logger.debug(f'LLM 原始响应类型: {type(response)}, 内容: {response}')
        
        # 如果 chat 已经返回了提取后的结果（字典包含 answer 和 cot），直接返回
        if isinstance(response, dict) and 'answer' in response and 'cot' in response:
            logger.debug(f'直接返回提取结果: answer长度={len(response.get("answer", ""))}, cot长度={len(response.get("cot", ""))}')
            return response
        
        # 使用统一的提取函数
        result = extract_answer_and_cot(response)
        
        # 记录提取结果（用于调试）
        logger.info(f'思维链提取结果: answer长度={len(result.get("answer", ""))}, cot长度={len(result.get("cot", ""))}')
        if not result.get('cot'):
            logger.warning(f'未提取到思维链，原始响应: {response}')
        
        return result

    def get_vision_response(self, prompt: str, base64_image: str, mime_type: str) -> Dict:
        """
        获取视觉模型响应
        :param prompt: 提示词
        :param base64_image: 图片的base64编码（不含前缀）
        :param mime_type: 图片的MIME类型
        :return: 包含answer和cot的字典
        """
        # 移除可能存在的 base64 前缀
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]
            
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        # 视觉模型通常不支持思维链，或者以不同方式支持
        # 这里先使用通用的 chat 接口
        response = self.chat(messages)
        
        if isinstance(response, dict) and 'answer' in response:
            return response
            
        return {'answer': str(response), 'cot': ''}
    
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

