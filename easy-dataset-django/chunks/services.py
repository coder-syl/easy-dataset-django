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
        # 参考 Node.js 逻辑：lib/file/text-splitter.js 第 176-180 行
        # 对于所有非 .md 文件，自动查找对应的 .md 文件（文件上传时会转换为 Markdown）
        project_path = Path('local-db') / project_id / 'files'
        file_path = project_path / file_name
        
        # 如果文件路径不以 .md 结尾，自动替换扩展名为 .md（与 Node.js 逻辑一致）
        if not file_name.endswith('.md'):
            import re
            # 使用正则表达式替换文件扩展名为 .md（与 Node.js 的 replace(/\.[^/.]+$/, '.md') 一致）
            md_file_name = re.sub(r'\.[^/.]+$', '.md', file_name)
            file_path = project_path / md_file_name
            logger.info(f'[{project_id}] 非 Markdown 文件，查找对应的 .md 文件: {file_name} -> {md_file_name}')
        
        # 检查文件是否存在
        if not file_path.exists():
            # 提供更详细的错误信息，帮助用户理解问题
            original_file_path = project_path / file_name
            error_msg = f'文件 {file_name} 不存在'
            if original_file_path.exists():
                error_msg += f'（原始文件存在，但未找到对应的 Markdown 文件: {file_path.name}。可能是文件转换失败，请检查上传日志）'
            else:
                error_msg += f'（也未找到对应的 Markdown 文件: {file_path.name}）'
            raise ValueError(error_msg)
        
        # 读取 Markdown 文件内容（UTF-8 编码，与 Node.js 的 readFile(filePath, 'utf8') 一致）
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # 验证文件内容不为空
        if not file_content or not file_content.strip():
            raise ValueError(f'文件 {file_name} 的内容为空，无法进行分割')
        
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
        
        # 验证分割结果不为空
        if not split_result or len(split_result) == 0:
            raise ValueError(f'文件 {file_name} 分割后没有生成任何文本块，请检查文件内容或分割参数')
        
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
        # 注意：Django 的 bulk_create 在 PostgreSQL 等数据库中会自动填充 id
        # 但在 SQLite 中可能不会，所以我们需要检查并处理
        created_chunks = Chunk.objects.bulk_create(chunks_to_create)
        logger.info(f'[{project_id}] 文件 {file_name} 分割完成, 创建 {len(created_chunks)} 个文本块')
        
        # 检查是否需要重新查询获取 id（SQLite 的情况）
        # 如果第一个创建的 chunk 没有 id，说明需要重新查询
        if created_chunks and (not hasattr(created_chunks[0], 'id') or created_chunks[0].id is None):
            # 重新查询获取 id（通过 name 和 file_id 匹配，按创建时间排序）
            created_chunks = list(Chunk.objects.filter(
                project=project,
                file_id=file_info.id,
                name__startswith=f"{base_name}-part-"
            ).order_by('name'))
            logger.debug(f'[{project_id}] 重新查询获取文本块 ID，共 {len(created_chunks)} 个')
        
        # 提取目录结构（简化版本）
        toc = extract_toc_from_markdown(file_content)
        
        # 保存TOC文件
        toc_dir = Path('local-db') / project_id / 'toc'
        toc_dir.mkdir(parents=True, exist_ok=True)
        toc_path = toc_dir / f"{base_name}-toc.json"
        with open(toc_path, 'w', encoding='utf-8') as f:
            json.dump({'toc': toc}, f, ensure_ascii=False, indent=2)
        logger.debug(f'[{project_id}] TOC文件已保存: {toc_path}')
        
        # 返回结果（与 Node.js 格式一致）
        return {
            'fileName': file_name,  # 原始文件名（与 Node.js 一致）
            'totalChunks': len(created_chunks),
            'chunks': [{
                'id': chunk.id,
                'name': chunk.name,
                'content': chunk.content,
                'summary': chunk.summary
            } for chunk in created_chunks],
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
    prompt = get_clean_prompt(language, original_content, project_id)
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

