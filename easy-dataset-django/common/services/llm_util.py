"""
LLM工具函数
用于提取思维链和答案
"""
import re
from typing import Dict, Tuple


def extract_think_chain(text: str) -> str:
    """
    从文本中提取思维链
    支持 <think> 和 <thinking> 标签
    :param text: 包含思维链标签的文本
    :return: 提取的思维链内容
    """
    start_tags = ['<think>', '<thinking>']
    end_tags = ['</think>', '</thinking>']
    
    start_index = -1
    end_index = -1
    used_start_tag = ''
    used_end_tag = ''
    
    # 查找第一个匹配的开始标签
    for i, start_tag in enumerate(start_tags):
        current_start_index = text.find(start_tag)
        if current_start_index != -1:
            start_index = current_start_index
            used_start_tag = start_tag
            used_end_tag = end_tags[i]
            break
    
    if start_index == -1:
        return ''
    
    # 查找对应的结束标签
    end_index = text.find(used_end_tag, start_index + len(used_start_tag))
    
    if end_index == -1:
        return ''
    
    # 提取思维链内容
    return text[start_index + len(used_start_tag):end_index].strip()


def extract_answer(text: str) -> str:
    """
    从文本中提取答案（去除思维链标签）
    支持 <think> 和 <thinking> 标签
    :param text: 包含思维链标签的文本
    :return: 提取的答案内容
    """
    start_tags = ['<think>', '<thinking>']
    end_tags = ['</think>', '</thinking>']
    
    result = text
    for i, start_tag in enumerate(start_tags):
        end_tag = end_tags[i]
        if start_tag in result and end_tag in result:
            # 移除思维链标签及其内容
            result = re.sub(
                re.escape(start_tag) + r'.*?' + re.escape(end_tag),
                '',
                result,
                flags=re.DOTALL
            )
    
    return result.strip()


def extract_answer_and_cot(llm_response: Dict) -> Dict[str, str]:
    """
    从LLM响应中提取答案和思维链
    支持多种格式：
    1. reasoning 字段
    2. <think> 或 <thinking> 标签
    3. OpenAI reasoning_content 字段
    :param llm_response: LLM响应字典
    :return: 包含 answer 和 cot 的字典
    """
    import logging
    logger = logging.getLogger(__name__)
    
    answer = ''
    cot = ''
    
    # 方式1: 从 reasoning 字段提取（某些模型直接返回）
    if 'reasoning' in llm_response and llm_response.get('reasoning'):
        cot = llm_response.get('reasoning', '')
        logger.debug(f'方式1: 从 reasoning 字段提取思维链，长度: {len(cot)}')
    
    # 方式2: 从 text/answer 字段中提取标签
    text = llm_response.get('text', '') or llm_response.get('answer', '') or ''
    
    if text:
        # 检查是否包含思维链标签（支持 <think> 和 <thinking>）
        if '<think>' in text or '<thinking>' in text:
            extracted_cot = extract_think_chain(text)
            extracted_answer = extract_answer(text)
            # 如果提取到了思维链，使用提取的结果
            if extracted_cot:
                cot = extracted_cot
                logger.debug(f'方式2: 从标签中提取思维链，长度: {len(cot)}')
            if extracted_answer:
                answer = extracted_answer
        else:
            # 如果没有标签，整个文本就是答案
            # 但也要检查是否包含思维链内容（某些模型可能在 content 中包含思维链）
            # 例如：以 "思考过程："、"推理：" 等开头的文本
            answer = text
    
    # 方式3: 从 OpenAI reasoning_content 字段提取（o1 系列模型）
    # 优先检查 response.body.choices[0].message
    if 'response' in llm_response:
        response_body = llm_response.get('response', {}).get('body', {})
        if 'choices' in response_body and len(response_body['choices']) > 0:
            message = response_body['choices'][0].get('message', {})
            
            # 提取 reasoning_content（优先使用，覆盖之前的结果）
            if 'reasoning_content' in message and message.get('reasoning_content'):
                cot = message.get('reasoning_content', '')
                logger.debug(f'方式3: 从 response.body.choices[0].message.reasoning_content 提取思维链，长度: {len(cot)}')
            
            # 检查其他可能的思维链字段（Qwen 模型可能使用不同的字段名）
            if not cot:
                # 检查 thinking 字段
                if 'thinking' in message and message.get('thinking'):
                    cot = message.get('thinking', '')
                    logger.debug(f'方式3.1: 从 message.thinking 提取思维链，长度: {len(cot)}')
                # 检查 reasoning 字段
                elif 'reasoning' in message and message.get('reasoning'):
                    cot = message.get('reasoning', '')
                    logger.debug(f'方式3.2: 从 message.reasoning 提取思维链，长度: {len(cot)}')
            
            # 提取 content（如果还没有答案，或者覆盖之前的结果）
            if 'content' in message and message.get('content'):
                answer = message.get('content', '')
        
        # 检查顶层是否有思维链相关字段（某些 API 可能在顶层返回）
        if not cot and 'thinking' in response_body:
            cot = response_body.get('thinking', '')
            logger.debug(f'方式3.3: 从 response.body.thinking 提取思维链，长度: {len(cot)}')
        elif not cot and 'reasoning' in response_body:
            cot = response_body.get('reasoning', '')
            logger.debug(f'方式3.4: 从 response.body.reasoning 提取思维链，长度: {len(cot)}')
    
    # 方式4: 直接从 choices 中提取（兼容不同响应格式）
    # 只有在前面没有提取到的情况下才尝试
    if not cot or not answer:
        # 尝试从顶层 choices 提取
        if 'choices' in llm_response and len(llm_response['choices']) > 0:
            message = llm_response['choices'][0].get('message', {})
            if not cot and 'reasoning_content' in message and message.get('reasoning_content'):
                cot = message.get('reasoning_content', '')
                logger.debug(f'方式4: 从顶层 choices[0].message.reasoning_content 提取思维链，长度: {len(cot)}')
            if not answer and 'content' in message and message.get('content'):
                answer = message.get('content', '')
    
    # 清理格式
    if answer and answer.startswith('\n\n'):
        answer = answer[2:]
    if cot and cot.endswith('\n\n'):
        cot = cot[:-2]
    
    result = {
        'answer': answer.strip(),
        'cot': cot.strip()
    }
    
    # 记录提取结果
    if not result['cot']:
        # 详细记录响应结构，帮助调试
        response_keys = list(llm_response.keys())
        has_response = 'response' in llm_response
        has_choices = 'choices' in llm_response
        has_reasoning = 'reasoning' in llm_response
        logger.debug(f'未提取到思维链。响应结构: keys={response_keys}, '
                    f'has_response={has_response}, has_choices={has_choices}, has_reasoning={has_reasoning}')
        
        # 如果 response.body 存在，记录其结构
        if has_response:
            body = llm_response.get('response', {}).get('body', {})
            if 'choices' in body and len(body['choices']) > 0:
                message = body['choices'][0].get('message', {})
                message_keys = list(message.keys())
                logger.debug(f'response.body.choices[0].message 的键: {message_keys}')
    
    return result

