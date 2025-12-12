"""
文件服务
处理文件相关业务逻辑
"""
import logging
from typing import List, Dict
from pathlib import Path
import json

from .models import UploadFile, GaPair
from projects.models import Project
from common.services.llm_service import LLMService
from common.services.prompt_service import get_question_prompt, get_ga_prompt, get_ga_generation_prompt

logger = logging.getLogger('files')


def batch_generate_ga_pairs(project_id: str, files: List[UploadFile], 
                           model_config: Dict, language: str = '中文',
                           append_mode: bool = False) -> List[Dict]:
    """
    批量生成GA对
    :param project_id: 项目ID
    :param files: 文件列表
    :param model_config: 模型配置
    :param language: 语言
    :param append_mode: 是否追加模式
    :return: 生成结果列表
    """
    logger.info(f'[{project_id}] 开始批量生成GA对: 文件数={len(files)}, 语言={language}, 追加模式={append_mode}')
    results = []
    
    for file_info in files:
        try:
            logger.info(f'[{project_id}] 开始处理文件: {file_info.file_name}')
            # 检查是否已存在GA对
            existing_pairs = GaPair.objects.filter(
                project_id=project_id,
                upload_file=file_info,
                is_active=True
            )
            
            if not append_mode and existing_pairs.exists():
                logger.info(f'[{project_id}] 文件 {file_info.file_name} 已存在GA对，跳过生成')
                results.append({
                    'fileId': file_info.id,
                    'fileName': file_info.file_name,
                    'success': True,
                    'skipped': True,
                    'message': 'GA pairs already exist',
                    'gaPairs': [{'id': p.id, 'genreTitle': p.genre_title, 'audienceTitle': p.audience_title} 
                               for p in existing_pairs]
                })
                continue
            
            # 读取文件内容
            project_path = Path('local-db') / project_id / 'files'
            file_path = project_path / file_info.file_name
            
            if not file_path.exists():
                logger.error(f'[{project_id}] 文件不存在: {file_path}')
                raise ValueError(f'文件 {file_info.file_name} 不存在')
            
            logger.debug(f'[{project_id}] 读取文件内容: {file_path}')
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # 限制内容长度
            max_length = 50000
            original_length = len(file_content)
            if len(file_content) > max_length:
                file_content = file_content[:max_length] + '...'
                logger.debug(f'[{project_id}] 文件内容过长，已截断: {original_length} -> {max_length} 字符')
            
            # 生成GA对
            logger.info(f'[{project_id}] 开始生成GA对: {file_info.file_name}')
            ga_pairs = generate_ga_pairs(file_content, project_id, language, model_config)
            logger.info(f'[{project_id}] GA对生成完成: {file_info.file_name}, 生成 {len(ga_pairs)} 个GA对')
            
            # 保存GA对
            saved_pairs = []
            for ga_pair_data in ga_pairs:
                if append_mode:
                    # 追加模式：检查是否已存在相同的GA对
                    existing = GaPair.objects.filter(
                        project_id=project_id,
                        upload_file=file_info,
                        genre_title=ga_pair_data['genre'],
                        audience_title=ga_pair_data['audience']
                    ).first()
                    
                    if existing:
                        existing.is_active = True
                        existing.save()
                        saved_pairs.append(existing)
                        continue
                
                # 确定pair_number（1-5）
                existing_count = GaPair.objects.filter(
                    project_id=project_id,
                    upload_file=file_info
                ).count()
                pair_number = min(existing_count + 1, 5)
                
                ga_pair = GaPair.objects.create(
                    project=file_info.project,
                    upload_file=file_info,
                    pair_number=pair_number,
                    genre_title=ga_pair_data['genre'],
                    genre_desc=ga_pair_data.get('genreDesc', ''),
                    audience_title=ga_pair_data['audience'],
                    audience_desc=ga_pair_data.get('audienceDesc', ''),
                    is_active=True
                )
                saved_pairs.append(ga_pair)
            
            logger.info(f'[{project_id}] 文件 {file_info.file_name} 处理完成, 保存了 {len(saved_pairs)} 个GA对')
            results.append({
                'fileId': file_info.id,
                'fileName': file_info.file_name,
                'success': True,
                'skipped': False,
                'message': f'Generated {len(saved_pairs)} GA pairs',
                'gaPairs': [{'id': p.id, 'genreTitle': p.genre_title, 'audienceTitle': p.audience_title} 
                           for p in saved_pairs]
            })
        except Exception as e:
            logger.error(f'[{project_id}] 文件 {file_info.file_name} 处理失败: {str(e)}', exc_info=True)
            results.append({
                'fileId': file_info.id,
                'fileName': file_info.file_name,
                'success': False,
                'skipped': False,
                'error': str(e),
                'message': f'Failed: {str(e)}'
            })
    
    success_count = len([r for r in results if r.get('success')])
    logger.info(f'[{project_id}] 批量生成GA对完成: 成功={success_count}, 失败={len(results) - success_count}, 总数={len(results)}')
    return results


def generate_ga_pairs(content: str, project_id: str, language: str, model_config: Dict) -> List[Dict]:
    """
    生成GA对（对齐 Node，使用 GA_GENERATION_PROMPT，自定义优先）
    :param content: 文件内容
    :param project_id: 项目ID
    :param language: 语言
    :param model_config: 模型配置
    :return: GA对列表
    """
    # 构建 GA 生成提示词（使用完整模板，优先自定义）
    prompt = get_ga_generation_prompt(language, content, project_id)

    # 调用 LLM
    llm_service = LLMService(model_config)
    response = llm_service.get_response_with_cot(prompt)
    answer = response.get('answer', '')

    # 解析 GA 对并规范化字段（兼容 {genre:{title,description}} 或扁平字段）
    def _normalize(item: Dict) -> Dict:
        genre = item.get('genre') or {}
        audience = item.get('audience') or {}
        return {
            'genreTitle': genre.get('title') or item.get('genreTitle') or item.get('genre') or '',
            'genreDesc': genre.get('description') or item.get('genreDesc') or '',
            'audienceTitle': audience.get('title') or item.get('audienceTitle') or item.get('audience') or '',
            'audienceDesc': audience.get('description') or item.get('audienceDesc') or ''
        }

    try:
        import re
        json_match = re.search(r'\[.*?\]', answer, re.DOTALL)
        if json_match:
            ga_pairs = json.loads(json_match.group())
        else:
            ga_pairs = json.loads(answer)

        if not isinstance(ga_pairs, list):
            ga_pairs = [ga_pairs]

        return [_normalize(p) for p in ga_pairs]
    except Exception:
        # 解析失败提供兜底
        return [
            {
                'genreTitle': '通用',
                'genreDesc': '通用内容',
                'audienceTitle': '一般用户',
                'audienceDesc': '一般用户群体'
            }
        ]

