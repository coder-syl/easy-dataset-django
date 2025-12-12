"""
文本块服务
处理文本分割和保存
"""
from pathlib import Path
import json
import logging
from typing import List, Dict

from .models import Chunk
from projects.models import Project
from files.models import UploadFile
from common.services.text_splitter import split_text_by_type
from common.services.llm_service import LLMService
from common.services.prompt_service import get_clean_prompt

logger = logging.getLogger('chunks')


def split_project_file(project_id: str, file_name: str) -> Dict:
    """
    分割项目文件
    :param project_id: 项目ID
    :param file_name: 文件名
    :return: 分割结果
    """
    try:
        project = Project.objects.get(id=project_id)
        file_info = UploadFile.objects.filter(project=project, file_name=file_name).first()
        
        if not file_info:
            raise ValueError(f'文件 {file_name} 不存在')
        
        # 读取文件内容
        project_path = Path('local-db') / project_id / 'files'
        file_path = project_path / file_name
        
        # 如果是PDF，查找对应的md文件
        if not file_path.exists() and file_name.endswith('.pdf'):
            md_file_name = file_name.replace('.pdf', '.md')
            file_path = project_path / md_file_name
        
        if not file_path.exists():
            raise ValueError(f'文件 {file_name} 不存在')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # 获取任务配置
        task_config_path = Path('local-db') / project_id / 'task-config.json'
        task_config = {}
        if task_config_path.exists():
            with open(task_config_path, 'r', encoding='utf-8') as f:
                task_config = json.load(f)
        
        # 获取分割参数
        split_type = task_config.get('splitType', 'markdown')
        chunk_size = task_config.get('chunkSize', 1500)
        chunk_overlap = task_config.get('chunkOverlap', 200)
        separator = task_config.get('separator', '\n\n')
        custom_separator = task_config.get('customSeparator', '---')
        
        # 分割文本
        split_result = split_text_by_type(
            file_content,
            split_type=split_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator=separator,
            custom_separator=custom_separator
        )
        
        # 先删除该文件已有的文本块（避免重复，与 Node.js 的 deleteChunksByFileId 逻辑一致）
        # 注意：这里需要先获取 chunk_ids，然后删除相关的问题，最后删除 chunks
        from questions.models import Question
        existing_chunks = Chunk.objects.filter(project=project, file_id=file_info.id)
        existing_chunk_ids = list(existing_chunks.values_list('id', flat=True))
        
        if existing_chunk_ids:
            # 删除相关的问题（与 Node.js 的 deleteChunksByFileId 逻辑一致）
            Question.objects.filter(chunk_id__in=existing_chunk_ids).delete()
            # 删除已有的文本块
            existing_chunks.delete()
            logger.info(f'[{project_id}] 已删除文件 {file_name} 的 {len(existing_chunk_ids)} 个旧文本块')
        
        # 保存文本块到数据库
        chunks_to_create = []
        base_name = Path(file_name).stem
        
        for index, part in enumerate(split_result):
            chunk_name = f"{base_name}-part-{index + 1}"
            chunk = Chunk(
                project=project,
                file_id=file_info.id,
                file_name=file_name,
                name=chunk_name,
                content=part.get('content', ''),
                summary=part.get('summary', ''),
                size=len(part.get('content', ''))
            )
            chunks_to_create.append(chunk)
        
        # 批量创建
        Chunk.objects.bulk_create(chunks_to_create)
        logger.info(f'[{project_id}] 文件 {file_name} 分割完成, 创建 {len(chunks_to_create)} 个文本块')
        
        # 提取目录结构（简化版本）
        toc = extract_toc_from_markdown(file_content)
        
        # 保存TOC文件
        toc_dir = Path('local-db') / project_id / 'toc'
        toc_dir.mkdir(parents=True, exist_ok=True)
        toc_path = toc_dir / f"{base_name}-toc.json"
        with open(toc_path, 'w', encoding='utf-8') as f:
            json.dump({'toc': toc}, f, ensure_ascii=False, indent=2)
        logger.debug(f'[{project_id}] TOC文件已保存: {toc_path}')
        
        return {
            'chunks': [{
                'id': chunk.id,
                'name': chunk.name,
                'content': chunk.content,
                'summary': chunk.summary
            } for chunk in chunks_to_create],
            'totalChunks': len(chunks_to_create),
            'toc': toc
        }
    except Exception as e:
        logger.error(f'[{project_id}] 分割文件 {file_name} 失败: {str(e)}', exc_info=True)
        raise Exception(f'分割文件失败: {str(e)}')


def extract_toc_from_markdown(text: str) -> str:
    """从Markdown文本中提取目录结构"""
    import re
    lines = text.split('\n')
    toc_lines = []
    
    for line in lines:
        # 匹配标题
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            indent = '  ' * (level - 1)
            toc_lines.append(f"{indent}- {title}")
    
    return '\n'.join(toc_lines)


def get_project_chunks(project_id: str, filter_type: str = '') -> Dict:
    """
    获取项目的所有文本块
    :param project_id: 项目ID
    :param filter_type: 过滤类型 (generated, ungenerated)
    :return: 文本块列表和文件结果
    """
    try:
        project = Project.objects.get(id=project_id)
        
        queryset = Chunk.objects.filter(project=project).exclude(
            name__in=['Image Chunk', 'Distilled Content']
        )
        
        if filter_type == 'generated':
            queryset = queryset.filter(questions__isnull=False).distinct()
        elif filter_type == 'ungenerated':
            queryset = queryset.filter(questions__isnull=True)
        
        chunks = queryset.all()
        
        # 按文件分组统计
        file_result = {}
        for chunk in chunks:
            file_name = chunk.file_name
            if file_name not in file_result:
                file_result[file_name] = {
                    'fileName': file_name,
                    'chunkCount': 0,
                    'questionCount': 0
                }
            file_result[file_name]['chunkCount'] += 1
        
        # 统计问题数量
        from questions.models import Question
        for file_name in file_result:
            file_chunks = Chunk.objects.filter(project=project, file_name=file_name)
            question_count = Question.objects.filter(
                project=project,
                chunk__in=file_chunks
            ).count()
            file_result[file_name]['questionCount'] = question_count
        
        # 获取目录结构（TOC）- 与 Node.js 保持一致
        from common.services.domain_tree import _get_project_tocs
        toc = _get_project_tocs(project_id)
        
        # 整合结果 - 与 Node.js 的 getProjectChunks 返回格式保持一致
        # Node.js 返回: { fileResult: { fileName, totalChunks, chunks, toc }, chunks }
        # 但实际 GET 接口返回: { chunks, ...fileResult, tags }，即 toc 在顶层
        file_result_obj = {
            'fileName': project.name + '.md' if hasattr(project, 'name') else 'project.md',
            'totalChunks': len(chunks),
            'chunks': [{
                'id': chunk.id,
                'name': chunk.name,
                'fileId': chunk.file_id,
                'fileName': chunk.file_name,
                'content': chunk.content,
                'summary': chunk.summary,
                'size': chunk.size
            } for chunk in chunks],
            'toc': toc
        }
        
        return {
            'chunks': [{
                'id': chunk.id,
                'name': chunk.name,
                'fileId': chunk.file_id,
                'fileName': chunk.file_name,
                'content': chunk.content,
                'summary': chunk.summary,
                'size': chunk.size
            } for chunk in chunks],
            'fileResult': file_result_obj
        }
    except Exception as e:
        raise Exception(f'获取文本块失败: {str(e)}')


def clean_chunk_content(project_id: str, chunk_id: str, model_config: Dict, language: str = '中文') -> Dict:
    """
    使用LLM清洗指定文本块内容
    """
    if not model_config:
        raise ValueError('模型配置不能为空')

    chunk = Chunk.objects.get(id=chunk_id, project_id=project_id)

    original_content = chunk.content or ''
    prompt = get_clean_prompt(language, original_content)
    llm = LLMService(model_config)
    resp = llm.get_response_with_cot(prompt)
    cleaned = (resp.get('answer') or '').strip()

    if not cleaned:
        raise ValueError('清洗结果为空')

    chunk.content = cleaned
    chunk.size = len(cleaned)
    chunk.save(update_fields=['content', 'size'])

    return {
        'chunkId': chunk.id,
        'originalLength': len(original_content),
        'cleanedLength': len(cleaned),
        'content': cleaned,
        # 记录LLM调用关键信息，便于任务日志展示
        'llm': {
            'model': model_config.get('model_name') or model_config.get('modelName') or model_config.get('model_id'),
            'provider': model_config.get('provider_id') or model_config.get('providerId'),
            'promptPreview': prompt[:100],
            'answerPreview': cleaned[:100],
            'raw': resp
        }
    }

