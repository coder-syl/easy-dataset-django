"""
图像数据集服务函数
"""
import re
import json
import logging
from pathlib import Path
import base64
from typing import Dict

from django.shortcuts import get_object_or_404
from projects.models import Project
from .models import ImageDataset
from common.services.llm_service import LLMService
from common.services.prompt_service import get_dataset_evaluation_prompt

logger = logging.getLogger(__name__)


def extract_json_from_llm_output(output: str):
    """从LLM输出中提取JSON"""
    try:
        # 尝试直接解析
        return json.loads(output)
    except:
        pass
    
    # 尝试提取JSON块
    json_match = re.search(r'\{[^{}]*\}', output, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass
    
    return None


def evaluate_image_dataset_service(project_id: str, dataset_id: str, model: Dict, language: str = 'zh-CN') -> Dict:
    """
    评估单个图像数据集的服务函数
    :param project_id: 项目ID
    :param dataset_id: 数据集ID
    :param model: 模型配置
    :param language: 语言
    :return: 评估结果字典，包含 success, score, evaluation 等字段
    """
    try:
        project = get_object_or_404(Project, id=project_id)
        dataset = get_object_or_404(ImageDataset, id=dataset_id, project=project)
        
        if not model:
            return {
                'success': False,
                'error': 'Model cannot be empty'
            }
        
        # 1. 获取图片信息（作为上下文）
        image_context = f'图片名称: {dataset.image_name}'
        
        # 2. 生成评估提示词（使用与文本数据集相同的评估提示词）
        # 注意：图像数据集没有原始文本块，所以传入空字符串
        prompt = get_dataset_evaluation_prompt(
            language,
            image_context,  # 使用图片信息作为上下文
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
        # 注意：ImageDataset 模型中没有 ai_evaluation 字段，只有 score
        dataset.score = score_val
        dataset.save(update_fields=['score'])
        
        return {
            'success': True,
            'datasetId': dataset_id,
            'score': score_val,
            'evaluation': evaluation
        }
    except Exception as e:
        logger.error(f'图像数据集评估失败: {str(e)}', exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

