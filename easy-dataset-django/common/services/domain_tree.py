import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from common.prompts.label import get_label_prompt
from common.prompts.label_revise import get_label_revise_prompt
from common.util.json_extract import extract_json_from_llm_output
from common.services.llm_service import LLMService
from tags.models import Tag

logger = logging.getLogger('common')


def _get_project_tocs(project_id: str) -> str:
    """
    获取项目的所有目录结构（类似 Node.js 的 getProjectTocs）
    """
    try:
        project_path = Path('local-db') / project_id
        toc_dir = project_path / 'toc'
        
        if not toc_dir.exists():
            return ''
        
        toc_by_file = {}
        toc = ''
        
        for toc_file in toc_dir.iterdir():
            if toc_file.name.endswith('-toc.json'):
                try:
                    with open(toc_file, 'r', encoding='utf-8') as f:
                        toc_data = json.load(f)
                    
                    file_name = toc_file.name.replace('-toc.json', '.md')
                    toc_by_file[file_name] = toc_data
                    
                    # 转换为 Markdown 格式的目录
                    # toc_data 可能是 {'toc': '...'} 格式（字符串）或 {'toc': [...]} 格式（列表）
                    if isinstance(toc_data, dict) and 'toc' in toc_data:
                        toc_content = toc_data['toc']
                        if isinstance(toc_content, str):
                            # 如果已经是字符串格式，直接使用
                            toc += f'### File：{file_name}\n'
                            toc += toc_content + '\n'
                        else:
                            # 如果是列表格式，转换为 Markdown
                            toc += f'### File：{file_name}\n'
                            toc += _toc_to_markdown(toc_content, is_nested=True) + '\n'
                    else:
                        # 兼容旧格式
                        toc += f'### File：{file_name}\n'
                        toc += _toc_to_markdown(toc_data, is_nested=True) + '\n'
                except Exception as e:
                    logger.warning(f'解析TOC文件 {toc_file.name} 出错: {e}', exc_info=True)
        
        return toc
    except Exception as e:
        logger.error(f'获取项目TOC出错: {e}', exc_info=True)
        return ''


def _toc_to_markdown(toc_data: Dict, is_nested: bool = True, indent: int = 0) -> str:
    """
    将TOC数据转换为Markdown格式
    """
    result = []
    if isinstance(toc_data, dict) and 'toc' in toc_data:
        toc_data = toc_data['toc']
    
    if isinstance(toc_data, list):
        for item in toc_data:
            if isinstance(item, dict):
                level = item.get('level', 1)
                title = item.get('title', '')
                children = item.get('children', [])
                
                prefix = '  ' * (level - 1)
                result.append(f'{prefix}- {title}')
                
                if children and is_nested:
                    result.append(_toc_to_markdown(children, is_nested, indent + 1))
    
    return '\n'.join(result)


def _filter_domain_tree(tree: List[Dict]) -> List[Dict]:
    """
    过滤领域树，移除 id、projectId、parentId、questionCount 等字段（类似 Node.js 的 filterDomainTree）
    """
    if not isinstance(tree, list):
        return []
    
    filtered = []
    for item in tree:
        if not isinstance(item, dict):
            continue
        
        # 创建新字典，只保留需要的字段
        filtered_item = {
            'label': item.get('label', '')
        }
        
        # 递归处理子节点
        if 'child' in item and item['child']:
            filtered_item['child'] = _filter_domain_tree(item['child'])
        elif 'children' in item and item['children']:
            filtered_item['child'] = _filter_domain_tree(item['children'])
        
        filtered.append(filtered_item)
    
    return filtered


def _batch_save_tags(project_id: str, tags: List[Dict]):
    """
    批量保存标签到数据库（类似 Node.js 的 batchSaveTags）
    """
    from projects.models import Project
    
    try:
        project = Project.objects.get(id=project_id)
        
        # 删除所有现有标签
        Tag.objects.filter(project=project).delete()
        
        # 递归插入标签
        _insert_tags(project, tags, parent=None)
    except Exception as e:
        raise Exception(f'保存标签失败: {str(e)}')


def _insert_tags(project, tags: List[Dict], parent: Optional[Tag] = None):
    """
    递归插入标签树
    """
    for tag_data in tags:
        if not isinstance(tag_data, dict) or 'label' not in tag_data:
            continue
        
        # 创建标签
        tag = Tag.objects.create(
            project=project,
            label=tag_data['label'],
            parent=parent
        )
        
        # 递归处理子节点
        children = tag_data.get('child') or tag_data.get('children', [])
        if children:
            _insert_tags(project, children, parent=tag)


def _get_tags(project_id: str) -> List[Dict]:
    """
    获取项目的所有标签（类似 Node.js 的 getTags）
    """
    try:
        tags = Tag.objects.filter(project_id=project_id, parent__isnull=True)
        return _tags_to_dict(tags)
    except Exception:
        return []


def _tags_to_dict(tags) -> List[Dict]:
    """
    将标签查询集转换为字典列表
    """
    result = []
    for tag in tags:
        tag_dict = {
            'id': tag.id,
            'label': tag.label,
            'projectId': tag.project_id,
            'parentId': tag.parent_id if tag.parent else None
        }
        
        # 递归处理子节点
        children = tag.children.all()
        if children.exists():
            tag_dict['child'] = _tags_to_dict(children)
        
        result.append(tag_dict)
    
    return result


def handle_domain_tree(
    project_id: str, 
    action: str, 
    all_toc: Optional[str] = None, 
    new_toc: Optional[str] = None, 
    delete_toc: Optional[str] = None, 
    model: Optional[Dict] = None, 
    language: str = '中文'
) -> List[Dict]:
    """
    处理领域树生成或更新（与 Node.js 的 handleDomainTree 保持一致）
    
    :param project_id: 项目ID
    :param action: 操作类型: 'rebuild', 'revise', 'keep'
    :param all_toc: 所有文档的目录结构
    :param new_toc: 新增文档的目录结构
    :param delete_toc: 删除文档的目录结构
    :param model: 使用的模型信息
    :param language: 语言: 'en' 或 '中文'
    :return: 生成的领域树标签
    """
    # 如果是保持不变，直接返回现有标签
    if action == 'keep':
        logger.info(f'[{project_id}] 使用现有领域树')
        return _get_tags(project_id)
    
    try:
        # 如果没有传入 all_toc，自动获取（类似 Node.js）
        if not all_toc:
            all_toc = _get_project_tocs(project_id)
        
        if not model:
            raise ValueError('模型配置不能为空')
        
        llm = LLMService({
            'provider_id': model.get('providerId') or model.get('provider_id') or '',
            'endpoint': model.get('endpoint', ''),
            'api_key': model.get('apiKey') or model.get('api_key') or '',
            'model_id': model.get('modelId') or model.get('model_id') or model.get('modelName') or model.get('model_name', ''),
            'temperature': model.get('temperature', 0.7),
            'max_tokens': model.get('maxTokens') or model.get('max_tokens', 2048),
            'top_p': model.get('topP') or model.get('top_p', 0.9),
            'top_k': model.get('topK') or model.get('top_k', 0)
        })
        
        tags = None
        prompt = ''
        
        # 重建领域树
        if action == 'rebuild':
            logger.info(f'[{project_id}] 正在重建领域树')
            # 限制文本长度为 100000 字符（与 Node.js 一致）
            text = all_toc[:100000] if all_toc else ''
            logger.debug(f'[{project_id}] TOC长度: {len(all_toc) if all_toc else 0}, 截断至: {len(text)}')
            prompt = get_label_prompt(language, {'text': text}, project_id)
            
            # 记录LLM调用开始
            logger.info(f'[{project_id}] 开始调用LLM API - 模型: {llm.model_id}, 提供商: {llm.provider_id}, 提示词长度: {len(prompt)} 字符')
            
            response = llm.get_response_with_cot(prompt)
            
            # 记录LLM响应
            response_text = response.get('answer') if isinstance(response, dict) else str(response)
            logger.info(f'[{project_id}] LLM API调用完成 - 响应长度: {len(response_text)} 字符')
            logger.debug(f'[{project_id}] LLM响应内容: {response_text[:500]}...' if len(response_text) > 500 else f'[{project_id}] LLM响应内容: {response_text}')
            
            tags = extract_json_from_llm_output(response_text)
            logger.info(f'[{project_id}] 重建完成，生成了 {len(tags) if tags else 0} 个标签')
            logger.debug(f'[{project_id}] 重建标签: {tags}')
        
        # 修订领域树
        elif action == 'revise':
            logger.info(f'[{project_id}] 正在修订领域树')
            # 获取现有的领域树
            existing_tags = _get_tags(project_id)
            
            if not existing_tags or len(existing_tags) == 0:
                # 如果没有现有领域树，就像重建一样处理
                logger.info(f'[{project_id}] 未找到现有标签，改为重建')
                text = all_toc[:100000] if all_toc else ''
                prompt = get_label_prompt(language, {'text': text}, project_id)
            else:
                # 增量更新领域树的逻辑
                logger.debug(f'[{project_id}] 找到 {len(existing_tags)} 个现有标签，执行修订')
                prompt = get_label_revise_prompt(
                    language,
                    {
                        'text': all_toc or '',
                        'existingTags': _filter_domain_tree(existing_tags),  # 过滤字段
                        'newContent': new_toc or '',
                        'deletedContent': delete_toc or ''
                    },
                    project_id
                )
            
            # 记录LLM调用开始
            logger.info(f'[{project_id}] 开始调用LLM API - 模型: {llm.model_id}, 提供商: {llm.provider_id}, 提示词长度: {len(prompt)} 字符')
            
            response = llm.get_response_with_cot(prompt)
            
            # 记录LLM响应
            response_text = response.get('answer') if isinstance(response, dict) else str(response)
            logger.info(f'[{project_id}] LLM API调用完成 - 响应长度: {len(response_text)} 字符')
            logger.debug(f'[{project_id}] LLM响应内容: {response_text[:500]}...' if len(response_text) > 500 else f'[{project_id}] LLM响应内容: {response_text}')
            
            tags = extract_json_from_llm_output(response_text)
            logger.info(f'[{project_id}] 修订完成，生成了 {len(tags) if tags else 0} 个标签')
            logger.debug(f'[{project_id}] 修订标签: {tags}')
        
        # 保存领域树标签（如果生成成功）
        if tags and isinstance(tags, list) and len(tags) > 0 and action != 'keep':
            logger.info(f'[{project_id}] 正在保存 {len(tags)} 个标签到数据库')
            _batch_save_tags(project_id, tags)
            logger.info(f'[{project_id}] 标签保存成功')
        elif not tags and action != 'keep':
            logger.warning(f'[{project_id}] 生成领域树标签失败')
        
        return tags if tags else []
        
    except Exception as e:
        logger.error(f'[{project_id}] 处理领域树时出错: {str(e)}', exc_info=True)
        raise e
