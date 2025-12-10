"""
数据集服务
处理数据集生成逻辑
"""
from typing import Dict, Optional
from nanoid import generate

from .models import Dataset
from projects.models import Project
from questions.models import Question
from chunks.models import Chunk
from llm.models import ModelConfig
from common.services.llm_service import LLMService


def generate_dataset_for_question(project_id: str, question_id: str, options: Dict) -> Dict:
    """
    为单个问题生成答案并创建数据集
    :param project_id: 项目ID
    :param question_id: 问题ID
    :param options: 选项，包含model和language
    :return: 生成的数据集
    """
    try:
        model_config = options.get('model')
        language = options.get('language', '中文')
        
        if not model_config:
            raise ValueError('模型配置不能为空')
        
        # 获取问题
        question = Question.objects.get(id=question_id, project_id=project_id)
        
        # 获取文本块
        chunk = Chunk.objects.get(id=question.chunk_id)
        
        # 创建LLM服务
        llm_service = LLMService(model_config)
        
        # 构建提示词
        from common.services.prompt_service import build_answer_prompt
        prompt = build_answer_prompt(language, {
            'text': chunk.content,
            'question': question.question
        }, project_id)
        
        # 调用LLM生成答案
        response = llm_service.get_response_with_cot(prompt)
        answer = response.get('answer', '')
        cot = response.get('cot', '')
        
        # 创建数据集
        dataset = Dataset.objects.create(
            id=generate(size=12),
            project_id=project_id,
            question_id=question_id,
            question=question.question,
            answer=answer,
            cot=cot if cot else '',
            chunk_name=chunk.name,
            chunk_content=chunk.content,
            model=model_config.get('model_name', ''),
            question_label=question.label or '',
            confirmed=False
        )
        
        # 更新问题状态
        question.answered = True
        question.save()
        
        return {
            'id': dataset.id,
            'question': dataset.question,
            'answer': dataset.answer,
            'cot': dataset.cot
        }
    except Exception as e:
        raise Exception(f'生成数据集失败: {str(e)}')



