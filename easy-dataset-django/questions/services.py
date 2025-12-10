"""
问题服务
处理问题生成相关业务逻辑
"""
from typing import Dict, List, Optional
from nanoid import generate
import json

from .models import Question
from projects.models import Project
from chunks.models import Chunk
from files.models import GaPair
from tags.models import Tag
from common.services.llm_service import LLMService
from common.services.prompt_service import get_question_prompt, get_ga_prompt, get_label_prompt


def generate_questions_for_chunk(project_id: str, chunk_id: str, options: Dict) -> Dict:
    """
    为文本块生成问题
    :param project_id: 项目ID
    :param chunk_id: 文本块ID
    :param options: 选项，包含model, language, count, gaPairId
    :return: 生成结果
    """
    model = options.get('model')
    language = options.get('language', '中文')
    count = options.get('count', 5)
    ga_pair_id = options.get('gaPairId')
    
    if not model:
        raise ValueError('模型配置不能为空')
    
    # 获取文本块
    chunk = Chunk.objects.get(id=chunk_id, project_id=project_id)
    
    # 获取GA对（如果有）
    active_ga_pair = None
    ga_prompt = ''
    if ga_pair_id:
        ga_pair = GaPair.objects.filter(
            id=ga_pair_id,
            project_id=project_id,
            file_id=chunk.file_id,
            active=True
        ).first()
        
        if ga_pair:
            active_ga_pair = {
                'genre': ga_pair.genre_title,
                'audience': ga_pair.audience_title
            }
            ga_prompt = get_ga_prompt(language, ga_pair.genre_title, ga_pair.audience_title)
    
    # 构建问题生成提示词
    prompt = get_question_prompt(
        language,
        chunk.content,
        count,
        ga_prompt,
        project_id
    )
    
    # 创建LLM服务
    llm_service = LLMService(model)
    
    # 调用LLM生成问题
    response = llm_service.get_response_with_cot(prompt)
    answer = response.get('answer', '')
    
    # 解析问题列表
    questions = parse_questions_from_response(answer)
    
    if not questions or len(questions) == 0:
        raise ValueError('生成问题失败或问题列表为空')
    
    # 标签分配：获取项目标签，使用LLM分配；若失败/无标签则回退为空
    label_map = {}
    project_labels = list(Tag.objects.filter(project_id=project_id).values_list('label', flat=True))
    if project_labels:
        try:
            label_prompt = get_label_prompt(language, project_labels, questions)
            label_resp = llm_service.get_response_with_cot(label_prompt)
            label_answer = label_resp.get('answer') or ''
            parsed_labels = json.loads(label_answer)
            if isinstance(parsed_labels, list):
                for item in parsed_labels:
                    if isinstance(item, dict):
                        q_text = item.get('question')
                        q_label = item.get('label') or ''
                        if q_text:
                            label_map[q_text] = q_label
        except Exception:
            label_map = {}
    
    # 保存问题
    project = Project.objects.get(id=project_id)
    saved_questions = []
    
    for question_text in questions:
        assigned_label = label_map.get(question_text, '')
        question = Question.objects.create(
            id=generate(size=12),
            project=project,
            chunk=chunk,
            question=question_text,
            ga_pair_id=ga_pair_id if ga_pair_id else None,
            answered=False,
            label=assigned_label
        )
        saved_questions.append({
            'id': question.id,
            'question': question.question,
            'chunkId': question.chunk_id,
            'label': question.label
        })
    
    return {
        'chunkId': chunk.id,
        'chunkName': chunk.name,
        'questions': saved_questions,
        'total': len(saved_questions),
        # 记录LLM调用关键信息，便于任务日志与前端展示
        'llm': {
            'model': model.get('model_name') or model.get('modelName') or model.get('model_id'),
            'provider': model.get('provider_id') or model.get('providerId'),
            'promptPreview': prompt[:100],
            'answerPreview': answer[:100],
            'raw': response
        }
    }


def generate_questions_for_chunk_with_ga(project_id: str, chunk_id: str, options: Dict) -> Dict:
    """
    兼容 GA 扩展的批量生成问题接口。
    当前实现复用基础的生成逻辑，并标记返回值，避免路由导入报错。
    """
    # 兼容 number/count 两种入参
    if 'count' not in options and 'number' in options:
        options = {**options, 'count': options['number']}
    result = generate_questions_for_chunk(project_id, chunk_id, options)
    if result is None:
        return None
    result['gaExpansionUsed'] = True
    result['gaPairsCount'] = result.get('gaPairsCount', 0)
    return result


def parse_questions_from_response(response: str) -> List[str]:
    """从LLM响应中解析问题列表"""
    import json
    import re
    
    try:
        # 尝试直接解析JSON
        questions = json.loads(response)
        if isinstance(questions, list):
            return [str(q) for q in questions]
    except:
        pass
    
    # 尝试提取JSON数组
    json_match = re.search(r'\[.*?\]', response, re.DOTALL)
    if json_match:
        try:
            questions = json.loads(json_match.group())
            if isinstance(questions, list):
                return [str(q) for q in questions]
        except:
            pass
    
    # 尝试提取引号中的内容
    questions = re.findall(r'"([^"]+)"', response)
    if questions:
        return questions
    
    # 如果都失败，按行分割
    lines = response.split('\n')
    questions = [line.strip('- ').strip() for line in lines if line.strip() and ('?' in line or '？' in line)]
    return questions[:20]  # 最多返回20个

