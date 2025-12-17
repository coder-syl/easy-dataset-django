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
from common.services.prompt_service import (
    get_assistant_reply_prompt,
    get_next_question_prompt
)


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

        # 初始化对话消息（用于模型上下文）
        messages: List[Dict] = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})

        # 用于记录最终保存的数据（角色名为自定义角色）
        conversation_messages: List[Dict] = []
        current_round = 0
        user_message = question.question  # 第一轮用户问题

        while current_round < rounds:
            # 用户发言
            messages.append({'role': 'user', 'content': user_message})
            conversation_messages.append({'role': role_a, 'content': user_message})

            # 构造助手回复提示词（支持项目自定义提示词）
            assistant_prompt = get_assistant_reply_prompt(
                language=language,
                scenario=scenario,
                role_a=role_a,
                role_b=role_b,
                chunk_content=chunk.content,
                conversation_history=_format_conversation_history(conversation_messages, role_a, role_b),
                current_round=current_round + 1,
                total_rounds=rounds,
                project_id=project_id
            )
            assistant_resp = llm_service.chat([{'role': 'user', 'content': assistant_prompt}]) or {}
            assistant_message = assistant_resp.get('answer', '') or assistant_resp.get('text', '')

            messages.append({'role': 'assistant', 'content': assistant_message})
            conversation_messages.append({'role': role_b, 'content': assistant_message})

            current_round += 1

            # 生成下一轮用户问题
            if current_round < rounds:
                next_question_prompt = get_next_question_prompt(
                    language=language,
                    scenario=scenario,
                    role_a=role_a,
                    role_b=role_b,
                    chunk_content=chunk.content,
                    conversation_history=_format_conversation_history(conversation_messages, role_a, role_b),
                    next_round=current_round + 1,
                    total_rounds=rounds,
                    project_id=project_id
                )
                next_resp = llm_service.chat([{'role': 'user', 'content': next_question_prompt}]) or {}
                user_message = next_resp.get('answer', '') or next_resp.get('text', '')

        # 创建对话数据集（补充模型名、轮数、场景等字段）
        conversation = DatasetConversation.objects.create(
            id=generate(size=12),
            project_id=project_id,
            question_id=question_id,
            question=question.question,
            chunk_id=question.chunk_id,
            model=model.get('modelName') or model.get('model_name') or '',
            raw_messages=json.dumps(conversation_messages, ensure_ascii=False),
            role_a=role_a,
            role_b=role_b,
            scenario=scenario,
            turn_count=current_round,
            max_turns=rounds,
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


def _format_conversation_history(conversation_history: List[Dict], role_a: str, role_b: str) -> str:
    """
    将对话历史格式化为文本，使用自定义角色名（与 Node 侧保持一致）
    """
    formatted = []
    for msg in conversation_history:
        role_name = role_a if msg.get('role') == role_a else role_b
        formatted.append(f"{role_name}: {msg.get('content', '')}")
    return "\n\n".join(formatted)

