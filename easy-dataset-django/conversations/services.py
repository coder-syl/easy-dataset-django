"""
多轮对话服务
处理多轮对话生成逻辑
"""
from typing import Dict, List
from nanoid import generate
import json

from .models import DatasetConversation
from projects.models import Project
from questions.models import Question
from chunks.models import Chunk
from common.services.llm_service import LLMService


def generate_multi_turn_conversation(project_id: str, question_id: str, config: Dict) -> Dict:
    """
    生成多轮对话数据集
    :param project_id: 项目ID
    :param question_id: 问题ID
    :param config: 配置，包含systemPrompt, scenario, rounds, roleA, roleB, model, language
    :return: 生成的对话数据集
    """
    try:
        system_prompt = config.get('systemPrompt', '')
        scenario = config.get('scenario', '')
        rounds = config.get('rounds', 3)
        role_a = config.get('roleA', '用户')
        role_b = config.get('roleB', '助手')
        model = config.get('model')
        language = config.get('language', '中文')
        
        if not model:
            raise ValueError('模型配置不能为空')
        
        # 获取问题
        question = Question.objects.get(id=question_id, project_id=project_id)
        
        # 获取文本块
        chunk = Chunk.objects.get(id=question.chunk_id)
        
        # 创建LLM服务
        llm_service = LLMService(model)
        
        # 初始化对话消息
        messages = []
        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt
            })
        
        # 生成多轮对话
        conversation_messages = []
        current_round = 0
        user_message = question.question
        
        while current_round < rounds:
            # 添加用户消息
            messages.append({
                'role': 'user',
                'content': user_message
            })
            conversation_messages.append({
                'role': role_a,
                'content': user_message
            })
            
            # 生成助手回复
            response = llm_service.chat(messages)
            assistant_message = response.get('answer', '')
            
            messages.append({
                'role': 'assistant',
                'content': assistant_message
            })
            conversation_messages.append({
                'role': role_b,
                'content': assistant_message
            })
            
            # 生成下一轮用户问题
            if current_round < rounds - 1:
                next_question_prompt = build_next_question_prompt(
                    conversation_messages, chunk.content, scenario, role_a, role_b, language
                )
                next_response = llm_service.chat([{'role': 'user', 'content': next_question_prompt}])
                user_message = next_response.get('answer', '') or next_response.get('text', '')
            
            current_round += 1
        
        # 创建对话数据集
        conversation = DatasetConversation.objects.create(
            id=generate(size=12),
            project_id=project_id,
            question_id=question_id,
            question=question.question,
            raw_messages=json.dumps(conversation_messages),
            role_a=role_a,
            role_b=role_b,
            scenario=scenario,
            confirmed=False
        )
        
        return {
            'success': True,
            'data': {
                'id': conversation.id,
                'messages': conversation_messages
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def build_next_question_prompt(conversation_history: List[Dict], content: str, 
                               scenario: str, role_a: str, role_b: str, language: str) -> str:
    """构建下一轮问题的提示词"""
    if language == 'en':
        prompt = f"""Based on the conversation history and content, generate the next question from {role_a}.

Content:
{content}

Conversation History:
{json.dumps(conversation_history, ensure_ascii=False, indent=2)}

Scenario: {scenario}

Please generate the next question that {role_a} would ask:"""
    else:
        prompt = f"""根据对话历史和内容，生成{role_a}的下一轮问题。

内容：
{content}

对话历史：
{json.dumps(conversation_history, ensure_ascii=False, indent=2)}

场景：{scenario}

请生成{role_a}会问的下一轮问题："""
    
    return prompt

