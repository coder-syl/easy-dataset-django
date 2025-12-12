"""
问题服务
处理问题生成相关业务逻辑
"""
from typing import Dict, List, Optional
from nanoid import generate
import json
import re
import logging

from .models import Question
from projects.models import Project
from chunks.models import Chunk
from files.models import GaPair
from tags.models import Tag
from common.services.llm_service import LLMService
from common.services.prompt_service import get_question_prompt, get_ga_prompt, get_label_prompt

logger = logging.getLogger(__name__)


def extract_json_from_llm_output(output: str):
    """
    从 LLM 输出中提取 JSON（与 Node.js 的 extractJsonFromLLMOutput 保持一致）
    处理包含 ```json 代码块的情况
    :param output: LLM 输出内容
    :return: 解析后的 JSON 对象，如果解析失败返回 None
    """
    if not output or not isinstance(output, str):
        return None
    
    output = output.strip()
    
    # 处理 <think> 标签（如果存在）
    if output.startswith('<think') or output.startswith('<thinking'):
        # 提取 <think> 标签后的内容
        think_end = output.find('</thinking>')
        if think_end == -1:
            think_end = output.find('</think>')
        if think_end != -1:
            output = output[think_end + len('</thinking>'):].strip()
    
    # 1. 尝试直接解析 JSON
    try:
        return json.loads(output)
    except:
        pass
    
    # 2. 尝试提取 ```json 代码块中的内容（使用非贪婪匹配，匹配第一个代码块）
    json_match = re.search(r'```json\s*([\s\S]*?)```', output, re.MULTILINE | re.DOTALL)
    if json_match:
        json_string = json_match.group(1).strip()
        try:
            return json.loads(json_string)
        except Exception as e:
            logger.debug(f'解析 ```json 代码块失败: {str(e)}, 内容: {json_string[:100]}')
            # 尝试修复常见的 JSON 问题（如末尾逗号）
            try:
                # 移除末尾的逗号
                json_string = re.sub(r',\s*}', '}', json_string)
                json_string = re.sub(r',\s*]', ']', json_string)
                return json.loads(json_string)
            except:
                pass
    
    # 3. 尝试提取 ``` 代码块中的内容（可能是 json 但没有标记）
    code_block_match = re.search(r'```\s*([\s\S]*?)```', output, re.MULTILINE | re.DOTALL)
    if code_block_match:
        json_string = code_block_match.group(1).strip()
        # 移除可能的语言标记（如 json, python 等）
        json_string = re.sub(r'^(json|python|javascript)\s*', '', json_string, flags=re.IGNORECASE)
        try:
            return json.loads(json_string)
        except:
            pass
    
    # 4. 尝试提取 JSON 数组（匹配最外层的数组）
    array_match = re.search(r'\[\s*[\s\S]*?\]', output, re.MULTILINE | re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except:
            pass
    
    # 5. 如果都失败，记录错误
    logger.warning(f'无法从 LLM 输出中提取 JSON: {output[:200]}')
    return None


def extract_labels(tags_data):
    """
    提取标签树结构（与 Node.js 的 extractLabels 保持一致）
    :param tags_data: 标签树数据（列表）
    :return: 提取后的标签树结构
    """
    if not isinstance(tags_data, list):
        return []
    
    result = []
    for item in tags_data:
        extracted = {
            'label': item.get('label', '')
        }
        
        # 递归处理子标签
        if 'child' in item and isinstance(item['child'], list) and len(item['child']) > 0:
            extracted['child'] = extract_labels(item['child'])
        
        result.append(extracted)
    
    return result


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
    
    # 标签分配：获取项目标签树，使用LLM分配；若失败/无标签则回退为空（与 Node.js 保持一致）
    label_map = {}
    try:
        # 获取项目对象
        project = Project.objects.get(id=project_id)
        
        # 获取所有标签
        all_tags = Tag.objects.filter(project_id=project_id)
        
        # 构建标签树（与 Node.js 的 getTags 保持一致）
        from tags.views import build_tag_tree
        tag_tree = build_tag_tree(list(all_tags), parent_id=None, project=project)
        
        # 提取标签树结构（与 Node.js 的 extractLabels 保持一致）
        simplified_tags = extract_labels(tag_tree)
        
        if simplified_tags:
            try:
                # 将标签树结构传给 LLM（与 Node.js 保持一致）
                label_prompt = get_label_prompt(language, simplified_tags, questions)
                label_resp = llm_service.get_response_with_cot(label_prompt)
                label_answer = label_resp.get('answer') or ''
                
                logger.debug(f'LLM 标签分配响应（前200字符）: {label_answer[:200]}')
                
                # 使用 extract_json_from_llm_output 提取 JSON（处理 ```json 代码块）
                parsed_labels = extract_json_from_llm_output(label_answer)
                
                if parsed_labels and isinstance(parsed_labels, list):
                    logger.info(f'成功解析 {len(parsed_labels)} 个标签分配结果')
                    for item in parsed_labels:
                        if isinstance(item, dict):
                            q_text = item.get('question')
                            q_label = item.get('label') or ''
                            if q_text:
                                label_map[q_text] = q_label
                                logger.debug(f'问题 "{q_text[:50]}..." -> 标签: "{q_label}"')
                    logger.info(f'成功构建标签映射，共 {len(label_map)} 个问题')
                else:
                    logger.warning(f'解析标签分配结果失败或结果不是列表: {type(parsed_labels)}, 原始响应: {label_answer[:200]}')
            except Exception as e:
                # 标签分配失败不影响主流程，只记录错误
                logger.warning(f'标签分配失败: {str(e)}', exc_info=True)
                label_map = {}
    except Exception as e:
        # 获取标签失败不影响主流程
        logger.warning(f'获取标签树失败: {str(e)}', exc_info=True)
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

