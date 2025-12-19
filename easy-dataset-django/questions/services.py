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
    
    # 调用LLM生成问题（与 Node.js 保持一致：使用 getResponse，返回字符串）
    answer = llm_service.get_response(prompt)
    
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
                # 将标签树结构传给 LLM（与 Node.js 保持一致：使用 getResponse，返回字符串）
                label_prompt = get_label_prompt(language, simplified_tags, questions, project_id)
                label_answer = llm_service.get_response(label_prompt)
                
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
        # 返回格式与 Node.js 保持一致：只包含 question 和 label
        saved_questions.append({
            'question': question_text,
            'label': assigned_label
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
            'raw': answer  # 使用 answer 而不是 response（与 Node.js 保持一致）
        }
    }


def generate_questions_for_chunk_with_ga(project_id: str, chunk_id: str, options: Dict) -> Dict:
    """
    GA 扩展模式：为每个激活的 GA 对生成问题（与 Node.js 实现保持一致）
    :param project_id: 项目ID
    :param chunk_id: 文本块ID
    :param options: 选项，包含model, language, number/count
    :return: 生成结果
    """
    model = options.get('model')
    language = options.get('language', '中文')
    number = options.get('number') or options.get('count', 5)
    
    if not model:
        raise ValueError('模型配置不能为空')
    
    # 获取文本块
    chunk = Chunk.objects.get(id=chunk_id, project_id=project_id)
    
    # 验证文本块内容
    if not chunk.content or len(chunk.content.strip()) == 0:
        raise ValueError(f'文本块 {chunk_id} 的内容为空，无法生成问题')
    
    logger.info(f'文本块内容长度: {len(chunk.content)}, 前100字符: {chunk.content[:100]}')
    
    # 获取任务配置
    from pathlib import Path
    import json
    import random
    project_root = Path('local-db') / project_id
    task_config_path = project_root / 'task-config.json'
    question_generation_length = 500  # 默认值
    question_mask_removing_probability = 60  # 默认值
    
    if task_config_path.exists():
        try:
            with open(task_config_path, 'r', encoding='utf-8') as f:
                task_config = json.load(f)
                question_generation_length = task_config.get('questionGenerationLength', 500)
                question_mask_removing_probability = task_config.get('questionMaskRemovingProbability', 60)
        except Exception as e:
            logger.warning(f'读取任务配置失败: {str(e)}')
    
    # 计算基础问题数量（与 Node.js 保持一致：使用 chunk.content.length）
    # Node.js: baseQuestionNumber = number || Math.floor(chunk.content.length / questionGenerationLength)
    # 注意：Node.js 可能返回 0，但 Django 使用 max(1, ...) 确保至少是 1，这是更安全的做法
    base_question_number = number if number is not None else max(1, len(chunk.content) // question_generation_length)
    
    def random_remove_question_mark(questions_list, probability):
        """随机移除问题中的问号（与 Node.js 保持一致）"""
        result = []
        for q in questions_list:
            # 与 Node.js 保持一致：使用 trimEnd()，只移除末尾空格
            question = q.rstrip()
            if random.random() * 100 < probability and (question.endswith('?') or question.endswith('？')):
                question = question[:-1]
            result.append(question)
        return result
    
    # 检查是否有可用的GA pairs并且启用GA扩展
    active_ga_pairs = []
    use_ga_expansion = False
    
    if chunk.file_id:
        try:
            active_ga_pairs = list(GaPair.objects.filter(
                upload_file_id=chunk.file_id,
                is_active=True
            ).order_by('pair_number'))
            use_ga_expansion = len(active_ga_pairs) > 0
            logger.info(f'检查到 {len(active_ga_pairs)} 个激活的GA pairs，{"启用" if use_ga_expansion else "不启用"}GA扩展生成')
        except Exception as e:
            logger.warning(f'获取GA pairs失败，使用标准生成: {str(e)}')
            use_ga_expansion = False
    
    # 创建LLM服务
    llm_service = LLMService(model)
    
    all_generated_questions = []
    total_expected_questions = base_question_number
    
    if use_ga_expansion:
        # GA扩展模式：为每个GA pair生成基础数量的问题
        total_expected_questions = base_question_number * len(active_ga_pairs)
        logger.info(
            f'GA扩展模式：将生成{base_question_number} 基础问题 × {len(active_ga_pairs)} GA pairs = {total_expected_questions}个总问题'
        )
        logger.info(f'激活的GA pairs列表: {[f"{p.genre_title}+{p.audience_title}" for p in active_ga_pairs]}')
        
        # 获取标签树（用于标签分配）
        label_map = {}
        try:
            project = Project.objects.get(id=project_id)
            all_tags = Tag.objects.filter(project_id=project_id)
            from tags.views import build_tag_tree
            tag_tree = build_tag_tree(list(all_tags), parent_id=None, project=project)
            simplified_tags = extract_labels(tag_tree)
        except Exception as e:
            logger.warning(f'获取标签树失败: {str(e)}')
            simplified_tags = []
        
        # 为每个GA pair生成问题
        for ga_pair in active_ga_pairs:
            try:
                # 构建 GA 提示词（与 Node.js 保持一致：传递包含描述的完整字符串）
                active_ga_pair_info = {
                    'genre': f"{ga_pair.genre_title}: {ga_pair.genre_desc}",
                    'audience': f"{ga_pair.audience_title}: {ga_pair.audience_desc}",
                    'active': ga_pair.is_active
                }
                # 与 Node.js 保持一致：传递包含描述的完整字符串
                ga_prompt = get_ga_prompt(language, active_ga_pair_info['genre'], active_ga_pair_info['audience'])
                
                # 生成问题提示词
                prompt = get_question_prompt(
                    language,
                    chunk.content,
                    base_question_number,
                    ga_prompt,
                    project_id
                )
                
                # 调用LLM生成问题（与 Node.js 保持一致：使用 getResponse，返回字符串）
                logger.info(f'GA pair {ga_pair.genre_title}+{ga_pair.audience_title} 开始生成问题，提示词长度: {len(prompt)}')
                logger.info(f'文本块内容长度: {len(chunk.content)}, 前200字符: {chunk.content[:200]}')
                logger.info(f'提示词中是否包含文本内容: {"{{text}}" not in prompt}')
                # 检查提示词中是否包含 {{text}} 占位符（不应该有）
                if '{{text}}' in prompt:
                    logger.error(f'警告：提示词中仍包含未替换的 {{text}} 占位符！')
                # 检查提示词中是否包含实际的文本块内容
                if chunk.content[:100] in prompt:
                    logger.info(f'✓ 提示词中包含文本块内容（前100字符匹配）')
                else:
                    logger.error(f'✗ 警告：提示词中不包含文本块内容！文本块前100字符: {chunk.content[:100]}')
                    logger.error(f'提示词中 "Text to Analyze" 或 "Analiz Edilecek Metin" 部分: {prompt[prompt.find("Text to Analyze"):prompt.find("Text to Analyze")+500] if "Text to Analyze" in prompt else (prompt[prompt.find("Analiz Edilecek Metin"):prompt.find("Analiz Edilecek Metin")+500] if "Analiz Edilecek Metin" in prompt else "未找到")}')
                logger.debug(f'提示词前1000字符: {prompt[:1000]}')
                logger.debug(f'提示词后1000字符: {prompt[-1000:] if len(prompt) > 1000 else prompt}')
                
                answer = llm_service.get_response(prompt)
                
                if not answer or len(answer.strip()) == 0:
                    logger.error(f'GA pair {ga_pair.genre_title}+{ga_pair.audience_title} LLM 返回为空')
                    continue
                
                logger.info(f'LLM 返回长度: {len(answer)}, 前200字符: {answer[:200]}')
                
                # 解析问题列表
                original_questions = parse_questions_from_response(answer)
                
                logger.info(f'解析后问题数量: {len(original_questions) if original_questions else 0}')
                if original_questions:
                    logger.debug(f'解析后的问题示例: {original_questions[0] if len(original_questions) > 0 else "N/A"}')
                
                if not original_questions or len(original_questions) == 0:
                    logger.warning(f'GA pair {ga_pair.genre_title}+{ga_pair.audience_title} 生成问题失败，跳过')
                    continue
                
                # 随机移除问号（与 Node.js 保持一致）
                questions = random_remove_question_mark(original_questions, question_mask_removing_probability)
                
                # 为这批问题添加标签（与 Node.js 保持一致：使用 getResponse，返回字符串）
                label_questions = []
                if simplified_tags:
                    try:
                        label_prompt = get_label_prompt(language, simplified_tags, questions)
                        logger.debug(f'标签分配提示词长度: {len(label_prompt)}')
                        
                        label_answer = llm_service.get_response(label_prompt)
                        
                        if not label_answer or len(label_answer.strip()) == 0:
                            logger.warning(f'标签分配 LLM 返回为空，使用空标签')
                            label_questions = [{'question': q, 'label': ''} for q in questions]
                        else:
                            logger.debug(f'标签分配 LLM 返回长度: {len(label_answer)}, 前200字符: {label_answer[:200]}')
                            parsed_labels = extract_json_from_llm_output(label_answer)
                            
                            if parsed_labels and isinstance(parsed_labels, list):
                                label_map = {}
                                for item in parsed_labels:
                                    if isinstance(item, dict):
                                        q_text = item.get('question')
                                        q_label = item.get('label') or ''
                                        if q_text:
                                            label_map[q_text] = q_label
                                
                                # 将标签应用到问题（确保只使用原始问题列表中的问题）
                                for q in questions:
                                    assigned_label = label_map.get(q, '')
                                    label_questions.append({
                                        'question': q,
                                        'label': assigned_label
                                    })
                                
                                logger.info(f'成功为 {len(label_questions)} 个问题分配标签')
                            else:
                                logger.warning(f'标签分配解析失败，返回格式不正确: {type(parsed_labels)}')
                                label_questions = [{'question': q, 'label': ''} for q in questions]
                    except Exception as e:
                        logger.error(f'标签分配失败: {str(e)}', exc_info=True)
                        label_questions = [{'question': q, 'label': ''} for q in questions]
                else:
                    label_questions = [{'question': q, 'label': ''} for q in questions]
                
                # 验证 label_questions 格式
                if not label_questions or len(label_questions) == 0:
                    logger.error(f'标签分配后问题列表为空，跳过保存')
                    continue
                
                # 验证每个问题对象格式
                for idx, q_item in enumerate(label_questions):
                    if not isinstance(q_item, dict):
                        logger.error(f'问题 {idx} 格式错误，不是字典: {q_item}')
                        continue
                    if 'question' not in q_item or not q_item['question']:
                        logger.error(f'问题 {idx} 缺少 question 字段或为空: {q_item}')
                        continue
                
                # 保存问题到数据库（关联GA pair）
                project = Project.objects.get(id=project_id)
                saved_for_ga_pair = []
                for q_item in label_questions:
                    question_text = q_item.get('question') if isinstance(q_item, dict) else q_item
                    assigned_label = q_item.get('label', '') if isinstance(q_item, dict) else ''
                    
                    question = Question.objects.create(
                        id=generate(size=12),
                        project=project,
                        chunk=chunk,
                        question=question_text,
                        ga_pair_id=str(ga_pair.id),
                        answered=False,
                        label=assigned_label
                    )
                    # 返回格式与 Node.js 保持一致：只包含 question, label, gaPairId, gaPairInfo
                    saved_for_ga_pair.append({
                        'question': question_text,
                        'label': assigned_label,
                        'gaPairId': str(ga_pair.id),
                        'gaPairInfo': f"{ga_pair.genre_title}+{ga_pair.audience_title}"
                    })
                
                all_generated_questions.extend(saved_for_ga_pair)
                logger.info(f'GA pair {ga_pair.genre_title}+{ga_pair.audience_title} 生成了 {len(saved_for_ga_pair)} 个问题')
                logger.info(f'当前总问题数: {len(all_generated_questions)} / 期望总数: {total_expected_questions}')
                
            except Exception as e:
                logger.error(f'为GA pair {ga_pair.genre_title}+{ga_pair.audience_title} 生成问题失败: {str(e)}', exc_info=True)
                continue
    else:
        # 标准模式：使用原有逻辑（与 Node.js 保持一致）
        logger.info(f'标准模式：生成 {base_question_number} 个问题')
        
        # 获取标签树（用于标签分配）
        simplified_tags = []
        try:
            project = Project.objects.get(id=project_id)
            all_tags = Tag.objects.filter(project_id=project_id)
            from tags.views import build_tag_tree
            tag_tree = build_tag_tree(list(all_tags), parent_id=None, project=project)
            simplified_tags = extract_labels(tag_tree)
        except Exception as e:
            logger.warning(f'获取标签树失败: {str(e)}')
        
        # 生成问题提示词
        prompt = get_question_prompt(
            language,
            chunk.content,
            base_question_number,
            '',
            project_id
        )
        
        # 验证提示词中包含文本块内容
        logger.info(f'标准模式：提示词长度: {len(prompt)}, 文本块内容长度: {len(chunk.content)}')
        if '{{text}}' in prompt:
            logger.error(f'警告：提示词中仍包含未替换的 {{text}} 占位符！')
        if chunk.content[:100] in prompt:
            logger.info(f'✓ 提示词中包含文本块内容（前100字符匹配）')
        else:
            logger.error(f'✗ 警告：提示词中不包含文本块内容！')
            # 查找提示词中 "Text to Analyze" 或类似部分
            text_section_start = prompt.find('Text to Analyze') if 'Text to Analyze' in prompt else (prompt.find('Analiz Edilecek Metin') if 'Analiz Edilecek Metin' in prompt else prompt.find('## Text to Analyze'))
            if text_section_start > 0:
                logger.error(f'提示词中文本部分（前500字符）: {prompt[text_section_start:text_section_start+500]}')
        
        # 调用LLM生成问题（与 Node.js 保持一致：使用 getResponse，返回字符串）
        answer = llm_service.get_response(prompt)
        
        if not answer or len(answer.strip()) == 0:
            raise ValueError('LLM 返回为空')
        
        # 解析问题列表
        original_questions = parse_questions_from_response(answer)
        
        if not original_questions or len(original_questions) == 0:
            raise ValueError('生成问题失败或问题列表为空')
        
        # 随机移除问号（与 Node.js 保持一致）
        questions = random_remove_question_mark(original_questions, question_mask_removing_probability)
        
        # 添加标签（与 Node.js 保持一致）
        label_questions = []
        if simplified_tags:
            try:
                label_prompt = get_label_prompt(language, simplified_tags, questions)
                label_answer = llm_service.get_response(label_prompt)
                
                if label_answer and len(label_answer.strip()) > 0:
                    parsed_labels = extract_json_from_llm_output(label_answer)
                    
                    if parsed_labels and isinstance(parsed_labels, list):
                        label_map = {}
                        for item in parsed_labels:
                            if isinstance(item, dict):
                                q_text = item.get('question')
                                q_label = item.get('label') or ''
                                if q_text:
                                    label_map[q_text] = q_label
                        
                        # 将标签应用到问题
                        for q in questions:
                            assigned_label = label_map.get(q, '')
                            label_questions.append({
                                'question': q,
                                'label': assigned_label
                            })
                    else:
                        label_questions = [{'question': q, 'label': ''} for q in questions]
                else:
                    label_questions = [{'question': q, 'label': ''} for q in questions]
            except Exception as e:
                logger.warning(f'标签分配失败: {str(e)}')
                label_questions = [{'question': q, 'label': ''} for q in questions]
        else:
            label_questions = [{'question': q, 'label': ''} for q in questions]
        
        # 保存问题到数据库（不关联GA pair）
        project = Project.objects.get(id=project_id)
        for q_item in label_questions:
            question_text = q_item.get('question') if isinstance(q_item, dict) else q_item
            assigned_label = q_item.get('label', '') if isinstance(q_item, dict) else ''
            
            Question.objects.create(
                id=generate(size=12),
                project=project,
                chunk=chunk,
                question=question_text,
                ga_pair_id=None,
                answered=False,
                label=assigned_label
            )
        
        all_generated_questions = label_questions
    
    # 返回生成的问题
    logger.info(f'问题生成完成：实际生成 {len(all_generated_questions)} 个问题，期望 {total_expected_questions} 个问题')
    if use_ga_expansion and len(all_generated_questions) < total_expected_questions:
        logger.warning(f'警告：GA扩展模式期望生成 {total_expected_questions} 个问题，但实际只生成了 {len(all_generated_questions)} 个问题')
    
    return {
        'chunkId': chunk_id,
        'questions': all_generated_questions,
        'total': len(all_generated_questions),
        'expectedTotal': total_expected_questions,
        'gaExpansionUsed': use_ga_expansion,
        'gaPairsCount': len(active_ga_pairs)
    }


def parse_questions_from_response(response: str) -> List[str]:
    """
    从LLM响应中解析问题列表（与 Node.js 保持一致）
    支持格式：
    1. 字符串数组: ["问题1", "问题2"]
    2. 对象数组: [{"question": "问题1"}, {"question": "问题2"}]
    3. 混合格式
    """
    import json
    import re
    
    def extract_question_text(q):
        """从问题对象或字符串中提取问题文本"""
        if isinstance(q, dict):
            # 如果是字典，尝试提取 question 字段
            return q.get('question', str(q))
        elif isinstance(q, str):
            return q
        else:
            return str(q)
    
    try:
        # 尝试直接解析JSON
        parsed = json.loads(response)
        if isinstance(parsed, list):
            return [extract_question_text(q) for q in parsed]
        elif isinstance(parsed, dict):
            # 如果是单个对象，尝试提取 question 字段
            if 'question' in parsed:
                return [extract_question_text(parsed)]
    except:
        pass
    
    # 尝试提取JSON数组
    json_match = re.search(r'\[.*?\]', response, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, list):
                return [extract_question_text(q) for q in parsed]
        except:
            pass
    
    # 尝试提取引号中的内容（简单字符串数组）
    questions = re.findall(r'"([^"]+)"', response)
    if questions:
        return questions
    
    # 如果都失败，按行分割
    lines = response.split('\n')
    questions = [line.strip('- ').strip() for line in lines if line.strip() and ('?' in line or '？' in line)]
    return questions[:20]  # 最多返回20个

