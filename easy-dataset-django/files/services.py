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
                upload_file=file_info
            )
            
            # 覆盖模式：删除旧的GA对（与 Node.js 保持一致）
            if not append_mode and existing_pairs.exists():
                logger.info(f'[{project_id}] 文件 {file_info.file_name} 已存在GA对，覆盖模式：删除旧的GA对')
                deleted_count = existing_pairs.delete()[0]
                logger.info(f'[{project_id}] 删除了 {deleted_count} 个旧的GA对')
            
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
            if append_mode:
                # 追加模式：检查是否已存在相同的GA对（与 Node.js 保持一致，但保留去重逻辑）
                existing_count = GaPair.objects.filter(
                    project_id=project_id,
                    upload_file=file_info
                ).count()
                start_pair_number = existing_count + 1
                new_pair_index = 0  # 用于计算新GA对的pair_number
                
                for index, ga_pair_data in enumerate(ga_pairs):
                    # 检查是否已存在相同的GA对
                    existing = GaPair.objects.filter(
                        project_id=project_id,
                        upload_file=file_info,
                        genre_title=ga_pair_data.get('genreTitle', ''),
                        audience_title=ga_pair_data.get('audienceTitle', '')
                    ).first()
                    
                    if existing:
                        existing.is_active = True
                        existing.save()
                        saved_pairs.append(existing)
                        continue
                    
                    # 创建新的GA对（pair_number 连续递增）
                    pair_number = start_pair_number + new_pair_index
                    new_pair_index += 1
                    ga_pair = GaPair.objects.create(
                        project=file_info.project,
                        upload_file=file_info,
                        pair_number=pair_number,
                        genre_title=ga_pair_data.get('genreTitle', ''),
                        genre_desc=ga_pair_data.get('genreDesc', ''),
                        audience_title=ga_pair_data.get('audienceTitle', ''),
                        audience_desc=ga_pair_data.get('audienceDesc', ''),
                        is_active=True
                    )
                    saved_pairs.append(ga_pair)
            else:
                # 覆盖模式：直接创建新的GA对（pair_number 从1开始）
                for index, ga_pair_data in enumerate(ga_pairs):
                    ga_pair = GaPair.objects.create(
                        project=file_info.project,
                        upload_file=file_info,
                        pair_number=index + 1,  # 1-5
                        genre_title=ga_pair_data.get('genreTitle', ''),
                        genre_desc=ga_pair_data.get('genreDesc', ''),
                        audience_title=ga_pair_data.get('audienceTitle', ''),
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
    生成GA对（对齐 Node.js，使用 GA_GENERATION_PROMPT，自定义优先）
    确保返回5个GA对，不足用fallback填充
    :param content: 文件内容
    :param project_id: 项目ID
    :param language: 语言
    :param model_config: 模型配置
    :return: GA对列表（确保5个）
    """
    # 构建 GA 生成提示词（使用完整模板，优先自定义）
    prompt = get_ga_generation_prompt(language, content, project_id)

    # 调用 LLM（与 Node.js 保持一致：使用 get_response，返回字符串）
    llm_service = LLMService(model_config)
    response_text = llm_service.get_response(prompt)

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

    # 使用健壮的JSON解析（与 Node.js 的 parseGaResponse 保持一致）
    try:
        from questions.services import extract_json_from_llm_output
        
        parsed = extract_json_from_llm_output(response_text)
        
        if not parsed:
            raise ValueError('Failed to extract JSON from LLM response')
        
        # 处理多种格式（与 Node.js 保持一致）
        ga_pairs_array = parsed
        if not isinstance(parsed, list):
            # 检查是否包装在对象中
            if isinstance(parsed, dict):
                if parsed.get('gaPairs') and isinstance(parsed['gaPairs'], list):
                    ga_pairs_array = parsed['gaPairs']
                elif parsed.get('pairs') and isinstance(parsed['pairs'], list):
                    ga_pairs_array = parsed['pairs']
                elif parsed.get('results') and isinstance(parsed['results'], list):
                    ga_pairs_array = parsed['results']
                else:
                    # 尝试转换扁平格式 (audience_1, genre_1 等)
                    object_keys = list(parsed.keys())
                    audience_keys = [k for k in object_keys if k.startswith('audience_')]
                    genre_keys = [k for k in object_keys if k.startswith('genre_')]
                    
                    if audience_keys and genre_keys:
                        ga_pairs_array = []
                        max_index = min(len(audience_keys), len(genre_keys))
                        for i in range(1, max_index + 1):
                            audience = parsed.get(f'audience_{i}')
                            genre = parsed.get(f'genre_{i}')
                            if audience and genre:
                                # 如果audience和genre是字符串，转换为对象格式
                                if isinstance(audience, str):
                                    audience = {'title': audience, 'description': ''}
                                if isinstance(genre, str):
                                    genre = {'title': genre, 'description': ''}
                                ga_pairs_array.append({'audience': audience, 'genre': genre})
                    else:
                        # 单个对象，转换为列表
                        ga_pairs_array = [parsed]
            else:
                ga_pairs_array = [parsed]
        
        # 验证和规范化
        validated_pairs = []
        for index, pair in enumerate(ga_pairs_array):
            try:
                normalized = _normalize(pair)
                # 验证必需字段
                if not normalized.get('genreTitle') or not normalized.get('audienceTitle'):
                    logger.warning(f'GA pair {index + 1} missing required fields, skipping')
                    continue
                validated_pairs.append(normalized)
            except Exception as e:
                logger.warning(f'Failed to normalize GA pair {index + 1}: {str(e)}')
                continue
        
        # 确保返回5个GA对（与 Node.js 保持一致）
        if len(validated_pairs) != 5:
            logger.warning(f'Expected 5 GA pairs, got {len(validated_pairs)}. Using first 5 or padding with fallbacks.')
            
            # 如果超过5个，取前5个
            if len(validated_pairs) > 5:
                validated_pairs = validated_pairs[:5]
            # 如果不足5个，用fallback填充
            elif len(validated_pairs) < 5:
                fallbacks = _get_fallback_ga_pairs()
                while len(validated_pairs) < 5:
                    validated_pairs.append(fallbacks[len(validated_pairs)])
        
        logger.info(f'Successfully parsed {len(validated_pairs)} GA pairs')
        return validated_pairs
        
    except Exception as e:
        logger.error(f'Failed to parse GA response: {str(e)}', exc_info=True)
        logger.error(f'Raw response (first 500 chars): {response_text[:500] if response_text else "None"}')
        
        # 返回fallback GA对（与 Node.js 保持一致）
        logger.info('Using fallback GA pairs due to parsing failure')
        return _get_fallback_ga_pairs()


def _get_fallback_ga_pairs() -> List[Dict]:
    """
    获取fallback GA对（与 Node.js 保持一致）
    :return: 5个默认GA对
    """
    return [
        {
            'genreTitle': '学术研究',
            'genreDesc': '学术性、研究导向的内容，具有正式的语调和详细的分析',
            'audienceTitle': '研究人员',
            'audienceDesc': '寻求深入知识的学术研究人员和研究生'
        },
        {
            'genreTitle': '教育指南',
            'genreDesc': '结构化的学习材料，具有清晰的解释和示例',
            'audienceTitle': '学生',
            'audienceDesc': '本科生和该主题的新学习者'
        },
        {
            'genreTitle': '专业手册',
            'genreDesc': '实用、以实施为重点的内容，用于工作场所应用',
            'audienceTitle': '从业者',
            'audienceDesc': '在实践中应用知识的行业专业人员'
        },
        {
            'genreTitle': '科普文章',
            'genreDesc': '使复杂主题易于理解的可访问内容',
            'audienceTitle': '普通公众',
            'audienceDesc': '没有专业背景的好奇读者'
        },
        {
            'genreTitle': '技术文档',
            'genreDesc': '详细的规范和实施指南',
            'audienceTitle': '开发人员',
            'audienceDesc': '技术专家和系统实施人员'
        }
    ]

