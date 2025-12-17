"""
数据集服务
处理数据集生成逻辑
"""
from typing import Dict, Optional
import json
from nanoid import generate
import logging

from .models import Dataset
from projects.models import Project
from questions.models import Question, QuestionTemplate
from chunks.models import Chunk
from files.models import GaPair
from llm.models import ModelConfig
from common.services.llm_service import LLMService

logger = logging.getLogger(__name__)


def safe_parse_json(text: str):
    """安全解析JSON"""
    try:
        return json.loads(text)
    except:
        return text


def extract_json_from_llm_output(output: str):
    """
    从LLM输出中提取JSON（类似Node.js的extractJsonFromLLMOutput）
    支持多种格式：纯JSON、代码块中的JSON等
    :param output: LLM输出文本
    :return: 解析后的JSON对象，如果失败返回None
    """
    if not output:
        return None
    
    # 去除首尾空白
    output = output.strip()
    
    # 如果输出以<think>或<think>开头，提取答案部分
    if output.startswith('<think') or output.startswith('<think>'):
        from common.services.llm_util import extract_answer
        output = extract_answer(output)
    
    # 尝试1: 直接解析JSON
    try:
        return json.loads(output)
    except:
        pass
    
    # 尝试2: 从```json代码块中提取
    import re
    json_match = re.search(r'```json\s*([\s\S]*?)```', output)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except:
            pass
    
    # 尝试3: 从```代码块中提取（没有json标记）
    json_match = re.search(r'```\s*([\s\S]*?)```', output)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except:
            pass
    
    # 尝试4: 查找第一个{到最后一个}之间的内容
    start_idx = output.find('{')
    end_idx = output.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(output[start_idx:end_idx + 1])
        except:
            pass
    
    # 尝试5: 使用jsonrepair修复（如果安装了）
    try:
        import jsonrepair
        repaired = jsonrepair.repair_json(output)
        return json.loads(repaired)
    except:
        pass
    
    return None


def evaluate_dataset_service(project_id: str, dataset_id: str, model: Dict, language: str = 'zh-CN') -> Dict:
    """
    评估单个数据集的服务函数
    :param project_id: 项目ID
    :param dataset_id: 数据集ID
    :param model: 模型配置
    :param language: 语言
    :return: 评估结果字典，包含 success, score, evaluation 等字段
    """
    from projects.models import Project
    from questions.models import Question
    from chunks.models import Chunk
    from django.shortcuts import get_object_or_404
    from common.services.llm_service import LLMService
    from common.services.prompt_service import get_dataset_evaluation_prompt
    import re
    
    try:
        project = get_object_or_404(Project, id=project_id)
        dataset = get_object_or_404(Dataset, id=dataset_id, project=project)
        
        if not model:
            return {
                'success': False,
                'error': 'Model cannot be empty'
            }
        
        # 1. 获取原始文本块内容
        chunk_content = dataset.chunk_content or ''
        
        # 如果数据集中没有chunk_content，尝试通过question_id查找
        if not chunk_content and dataset.question_id:
            try:
                question = Question.objects.filter(
                    id=dataset.question_id,
                    project_id=project_id
                ).first()
                
                if question and question.chunk:
                    chunk = question.chunk
                    # 检查是否是蒸馏内容
                    if chunk.name == 'Distilled Content':
                        chunk_content = 'Distilled Content - 没有原始文本参考'
                    else:
                        chunk_content = chunk.content or ''
            except Exception as e:
                logger.warning(f'无法获取原始文本块内容: {str(e)}')
                chunk_content = dataset.chunk_content or ''
        
        # 检查是否是蒸馏内容
        if dataset.chunk_name == 'Distilled Content' or 'Distilled Content' in chunk_content:
            chunk_content = 'Distilled Content - 没有原始文本参考'
        
        # 2. 生成评估提示词
        prompt = get_dataset_evaluation_prompt(
            language,
            chunk_content,
            dataset.question,
            dataset.answer,
            project_id
        )
        
        # 3. 调用LLM进行评估
        llm = LLMService(model)
        resp = llm.get_response_with_cot(prompt)
        answer = resp.get('answer') or ''
        
        # 4. 解析评估结果
        evaluation_result = extract_json_from_llm_output(answer)
        
        if not evaluation_result or not isinstance(evaluation_result.get('score'), (int, float)) or not evaluation_result.get('evaluation'):
            # 如果解析失败，尝试正则表达式提取
            score_match = re.search(r'([0-5](?:\.5)?)', answer)
            score_val = float(score_match.group(1)) if score_match else 0.0
            evaluation = answer
        else:
            score_val = float(evaluation_result.get('score', 0))
            evaluation = evaluation_result.get('evaluation', '')
        
        # 5. 验证和规范化评分
        # 确保评分在0-5范围内
        score_val = max(0.0, min(5.0, score_val))
        # 确保评分精确到0.5
        score_val = round(score_val * 2) / 2
        
        # 6. 更新数据集评估结果
        dataset.score = score_val
        dataset.ai_evaluation = evaluation
        dataset.save(update_fields=['score', 'ai_evaluation'])
        
        return {
            'success': True,
            'datasetId': dataset_id,
            'score': score_val,
            'evaluation': evaluation
        }
    except Exception as e:
        logger.error(f'数据集评估失败: {str(e)}', exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def get_question_template_prompts(question_template, language: str) -> Dict:
    """
    获取问题模板的提示词部分
    :param question_template: 问题模板对象
    :param language: 语言
    :return: 包含 templatePrompt 和 outputFormatPrompt 的字典
    """
    template_prompt = ''
    output_format_prompt = ''
    
    if question_template:
        # 描述
        if question_template.description:
            template_prompt = f'\n\n{question_template.description}'
        
        # 答案类型处理
        if question_template.answer_type == 'label':
            # 标签类型：需要从指定标签列表中选择
            labels_text = question_template.labels or '[]'
            if language == 'en':
                output_format_prompt = (
                    f' \n\n ## Output Format \n\n '
                    f'Final output must be a string array, and must be selected from the following array, '
                    f'if the answer is not in the target array, return: ["other"] '
                    f'No additional information can be added: \n\n{labels_text}'
                )
            else:
                output_format_prompt = (
                    f'\n\n ## 输出格式 \n\n '
                    f'最终输出必须是一个字符串数组，而且必须在以下数组中选择，'
                    f'如果答案不在目标数组中，返回：["其他"] 不得额外添加任何其他信息：\n\n{labels_text}'
                )
        elif question_template.answer_type == 'custom_format':
            # 自定义格式类型
            custom_format = question_template.custom_format or ''
            if language == 'en':
                output_format_prompt = (
                    f' \n\n ## Output Format \n\n '
                    f'Final output must strictly follow the following structure, '
                    f'no additional information can be added: \n\n{custom_format}'
                )
            else:
                output_format_prompt = (
                    f'\n\n ## 输出格式 \n\n '
                    f'最终输出必须严格遵循以下结构，不得额外添加任何其他信息：\n\n{custom_format}'
                )
    
    return {
        'templatePrompt': template_prompt,
        'outputFormatPrompt': output_format_prompt
    }


def optimize_cot(original_question: str, answer: str, original_cot: str, language: str, 
                 llm_service: LLMService, dataset_id: str, project_id: str) -> None:
    """
    优化思维链（异步处理，不阻塞主流程）
    :param original_question: 原始问题
    :param answer: 答案
    :param original_cot: 原始思维链
    :param language: 语言
    :param llm_service: LLM服务实例
    :param dataset_id: 数据集ID
    :param project_id: 项目ID
    """
    try:
        from common.services.prompt_service import get_optimize_cot_prompt
        prompt = get_optimize_cot_prompt(language, original_question, answer, original_cot, project_id)
        response = llm_service.get_response_with_cot(prompt)
        optimized_cot = response.get('answer', '') or response.get('cot', '')
        
        # 去除可能的"优化后的思维链"等前缀
        if optimized_cot:
            optimized_cot = optimized_cot.replace('优化后的思维链', '').replace('优化后的思维链：', '').strip()
        
        # 更新数据集
        Dataset.objects.filter(id=dataset_id).update(cot=optimized_cot)
        logger.info(f'成功优化思维链: {original_question}, ID: {dataset_id}')
    except Exception as e:
        logger.error(f'优化思维链失败: {str(e)}')
        # 优化失败不影响主流程，只记录错误


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
        chunk = question.chunk
        
        # 检查是否是蒸馏内容
        id_distill = chunk.name in ['Distilled Content', 'Image Chunk']
        
        # 获取问题模板（如果有）
        question_template = None
        answer_type = 'text'
        if question.template_id:
            try:
                question_template = QuestionTemplate.objects.get(id=question.template_id, project_id=project_id)
                answer_type = question_template.answer_type or 'text'
            except QuestionTemplate.DoesNotExist:
                pass
        
        # 创建LLM服务
        llm_service = LLMService(model_config)
        
        # 检查GA Pairs支持
        active_ga_pair = None
        use_enhanced_prompt = False
        active_pairs_count = 0
        
        if not id_distill and chunk.file_id:
            try:
                # 获取文件的激活GA对
                active_ga_pairs = GaPair.objects.filter(
                    upload_file_id=chunk.file_id,
                    is_active=True
                ).order_by('pair_number')
                active_pairs_count = active_ga_pairs.count()
                
                # 如果问题关联了GA对，使用该GA对
                if question.ga_pair_id:
                    try:
                        linked_ga_pair = GaPair.objects.get(
                            id=question.ga_pair_id,
                            upload_file_id=chunk.file_id,
                            is_active=True
                        )
                        active_ga_pair = {
                            'genre': f"{linked_ga_pair.genre_title}: {linked_ga_pair.genre_desc}",
                            'audience': f"{linked_ga_pair.audience_title}: {linked_ga_pair.audience_desc}",
                            'active': linked_ga_pair.is_active
                        }
                        use_enhanced_prompt = True
                        logger.info(f'问题关联GA pair: {linked_ga_pair.genre_title}+{linked_ga_pair.audience_title}')
                    except GaPair.DoesNotExist:
                        pass
                
                logger.info(f'检查到激活的GA对，{"使用" if use_enhanced_prompt else "不使用"}增强提示词')
            except Exception as e:
                logger.warn(f'获取GA pairs失败，使用标准提示词: {str(e)}')
                use_enhanced_prompt = False
        
        # 获取问题模板的提示词部分
        template_prompts = get_question_template_prompts(question_template, language)
        
        # 构建提示词
        if id_distill:
            # 对于蒸馏内容，直接使用问题
            prompt = question.question
        elif use_enhanced_prompt:
            # 使用MGA增强提示词
            from common.services.prompt_service import build_enhanced_answer_prompt
            prompt = build_enhanced_answer_prompt(language, {
                'text': chunk.content,
                'question': question.question,
                'templatePrompt': template_prompts['templatePrompt'],
                'outputFormatPrompt': template_prompts['outputFormatPrompt'],
                'activeGaPair': active_ga_pair
            }, project_id)
            logger.info('使用MGA增强提示词生成答案')
        else:
            # 使用标准提示词
            from common.services.prompt_service import build_answer_prompt
            prompt = build_answer_prompt(language, {
                'text': chunk.content,
                'question': question.question,
                'templatePrompt': template_prompts['templatePrompt'],
                'outputFormatPrompt': template_prompts['outputFormatPrompt']
            }, project_id)
            logger.info('使用标准提示词生成答案')
        
        # 调用LLM生成答案
        response = llm_service.get_response_with_cot(prompt)
        answer = response.get('answer', '')
        cot = response.get('cot', '')
        
        # 根据答案类型处理答案格式
        if answer_type != 'text' and answer:
            answer_json = safe_parse_json(answer)
            if not isinstance(answer_json, str):
                answer = json.dumps(answer_json, ensure_ascii=False, indent=2)
        
        # 创建数据集
        dataset = Dataset.objects.create(
            id=generate(size=12),
            project_id=project_id,
            question_id=question_id,
            question=question.question,
            answer=answer,
            cot=cot if cot else '',
            chunk_name=chunk.name,
            chunk_content='',  # 不再保存原始文本块内容（与 Node.js 对齐）
            model=model_config.get('model_name', '') or model_config.get('modelName', ''),
            question_label=question.label or '',
            answer_type=answer_type,
            confirmed=False
        )
        
        # 如果有思维链且不是蒸馏内容，异步优化思维链
        if cot and not id_distill:
            # 为了性能考虑，这里异步优化（实际可以放到后台任务中）
            try:
                optimize_cot(question.question, answer, cot, language, llm_service, dataset.id, project_id)
            except Exception as e:
                logger.warn(f'思维链优化失败（不影响主流程）: {str(e)}')
        
        # 更新问题状态
        question.answered = True
        question.save()
        
        log_message = f'成功生成{"MGA增强" if use_enhanced_prompt else "标准"}数据集: {question.question}'
        logger.info(log_message)
        
        return {
            'success': True,
            'dataset': {
                'id': dataset.id,
                'question': dataset.question,
                'answer': dataset.answer,
                'cot': dataset.cot,
                'answerType': dataset.answer_type
            },
            'mgaEnhanced': use_enhanced_prompt,
            'activePairs': active_pairs_count
        }
    except Exception as e:
        logger.error(f'生成数据集失败: {str(e)}')
        raise Exception(f'生成数据集失败: {str(e)}')


def optimize_dataset_service(project_id: str, dataset_id: str, question: str, answer: str, 
                             cot: str, advice: str, chunk_content: str, model: Dict, 
                             language: str = 'zh-CN') -> Dict:
    """
    优化数据集答案（与 Node.js 版本对齐）
    :param project_id: 项目ID
    :param dataset_id: 数据集ID
    :param question: 问题
    :param answer: 答案
    :param cot: 思维链
    :param advice: 优化建议
    :param chunk_content: 文本块内容
    :param model: 模型配置
    :param language: 语言
    :return: 优化结果字典
    """
    try:
        from django.shortcuts import get_object_or_404
        from .models import Dataset
        from projects.models import Project
        
        project = get_object_or_404(Project, id=project_id)
        dataset = get_object_or_404(Dataset, id=dataset_id, project=project)
        
        # 生成优化提示词
        from common.services.prompt_service import get_new_answer_prompt
        prompt = get_new_answer_prompt(language, chunk_content, question, answer, advice, project_id)
        
        # 调用LLM生成优化后的答案
        llm_service = LLMService(model)
        response = llm_service.get_response(prompt)
        
        # 从LLM输出中提取JSON格式的优化结果
        optimized_result = extract_json_from_llm_output(response)
        
        if not optimized_result or not optimized_result.get('answer'):
            return {
                'success': False,
                'error': 'Failed to optimize answer, please try again'
            }
        
        # 更新数据集
        dataset.answer = optimized_result.get('answer', answer)
        if cot:
            # 如果提供了思维链，更新思维链
            dataset.cot = optimized_result.get('cot', cot)
        dataset.save()
        
        # 返回优化后的数据集
        return {
            'success': True,
            'dataset': {
                'id': dataset.id,
                'question': dataset.question,
                'answer': dataset.answer,
                'cot': dataset.cot,
                'answerType': dataset.answer_type
            }
        }
    except Exception as e:
        logger.error(f'优化数据集失败: {str(e)}', exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


