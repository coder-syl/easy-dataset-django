"""
文本分割服务
基于apps/common/util/split_model.py
"""
import re
from typing import List, Dict
from pathlib import Path
import sys

# 添加apps路径到sys.path
apps_path = Path(__file__).parent.parent.parent.parent / 'apps'
if str(apps_path) not in sys.path:
    sys.path.insert(0, str(apps_path))

try:
    from common.util.split_model import SplitModel, default_split_pattern, get_split_model
except ImportError:
    # 如果导入失败，使用简化版本
    SplitModel = None
    default_split_pattern = None
    get_split_model = None


def split_markdown_text(text: str, min_length: int = 1500, max_length: int = 2000, 
                        with_filter: bool = True, limit: int = 100000) -> List[Dict]:
    """
    分割Markdown文本
    :param text: 文本内容
    :param min_length: 最小长度
    :param max_length: 最大长度
    :param with_filter: 是否过滤特殊字符
    :param limit: 每段大小限制
    :return: 分割后的段落列表
    """
    if SplitModel is None:
        # 简化版本：按段落分割
        paragraphs = text.split('\n\n')
        result = []
        current_chunk = ''
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > max_length and current_chunk:
                result.append({
                    'title': '',
                    'content': current_chunk.strip(),
                    'summary': ''
                })
                current_chunk = para
            else:
                current_chunk += '\n\n' + para if current_chunk else para
        
        if current_chunk:
            result.append({
                'title': '',
                'content': current_chunk.strip(),
                'summary': ''
            })
        
        return result
    
    # 使用apps中的SplitModel
    split_model = get_split_model('test.md', with_filter=with_filter, limit=limit)
    return split_model.parse(text)


def split_text_by_type(text: str, split_type: str = 'markdown', 
                       chunk_size: int = 1500, chunk_overlap: int = 200,
                       separator: str = '\n\n', custom_separator: str = '---') -> List[Dict]:
    """
    根据类型分割文本
    :param text: 文本内容
    :param split_type: 分割类型 (markdown, text, token, recursive, custom)
    :param chunk_size: 块大小
    :param chunk_overlap: 重叠大小
    :param separator: 分隔符
    :param custom_separator: 自定义分隔符
    :return: 分割后的块列表
    """
    if split_type == 'markdown':
        return split_markdown_text(text, min_length=chunk_size, max_length=chunk_size + 500)
    elif split_type == 'text':
        # 字符分块
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]
            chunks.append({
                'title': '',
                'content': chunk_text,
                'summary': ''
            })
            start = end - chunk_overlap
        return chunks
    elif split_type == 'custom':
        # 自定义分隔符分块
        parts = text.split(custom_separator)
        return [{
            'title': '',
            'content': part.strip(),
            'summary': ''
        } for part in parts if part.strip()]
    else:
        # 默认按段落分割
        return split_markdown_text(text)


def split_project_file(file_path: str, split_type: str = 'markdown', 
                       chunk_size: int = 1500, chunk_overlap: int = 200,
                       separator: str = '\n\n', custom_separator: str = '---') -> List[Dict]:
    """
    读取项目文件并按指定规则分割，兼容问题生成的旧接口。
    """
    path = Path(file_path)
    if not path.exists():
        return []
    
    text = path.read_text(encoding='utf-8', errors='ignore')
    return split_text_by_type(
        text,
        split_type=split_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separator=separator,
        custom_separator=custom_separator
    )
