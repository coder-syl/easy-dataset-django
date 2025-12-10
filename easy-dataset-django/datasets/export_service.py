"""
数据集导出服务
支持多种格式：JSON、CSV、JSONL等
"""
import json
import csv
from io import StringIO
from typing import List, Dict, Optional
from django.http import HttpResponse
from .models import Dataset
from tags.models import Tag


def export_datasets_to_json(datasets: List[Dataset], format_type: str = 'standard') -> str:
    """
    导出数据集为JSON格式
    :param datasets: 数据集列表
    :param format_type: 格式类型 ('standard', 'huggingface', 'llamafactory')
    :return: JSON字符串
    """
    if format_type == 'huggingface':
        # HuggingFace格式
        data = []
        for dataset in datasets:
            data.append({
                'instruction': dataset.question,
                'input': '',
                'output': dataset.answer
            })
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    elif format_type == 'llamafactory':
        # LLaMA Factory格式
        data = []
        for dataset in datasets:
            data.append({
                'instruction': dataset.question,
                'input': '',
                'output': dataset.answer,
                'history': []
            })
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    else:
        # 标准格式
        data = []
        for dataset in datasets:
            item = {
                'id': dataset.id,
                'question': dataset.question,
                'answer': dataset.answer,
                'chunkName': dataset.chunk_name,
                'model': dataset.model,
                'questionLabel': dataset.question_label,
                'cot': dataset.cot or '',
                'confirmed': dataset.confirmed,
                'score': dataset.score,
                'tags': json.loads(dataset.tags) if dataset.tags else [],
                'note': dataset.note or '',
                'other': json.loads(dataset.other) if dataset.other else {}
            }
            data.append(item)
        return json.dumps(data, ensure_ascii=False, indent=2)


def export_datasets_to_csv(datasets: List[Dataset]) -> str:
    """
    导出数据集为CSV格式
    :param datasets: 数据集列表
    :return: CSV字符串
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow(['question', 'answer', 'chunkName', 'model', 'questionLabel', 'cot', 'confirmed', 'score', 'tags', 'note'])
    
    # 写入数据
    for dataset in datasets:
        tags_str = dataset.tags if dataset.tags else '[]'
        writer.writerow([
            dataset.question,
            dataset.answer,
            dataset.chunk_name or '',
            dataset.model or '',
            dataset.question_label or '',
            dataset.cot or '',
            'true' if dataset.confirmed else 'false',
            dataset.score,
            tags_str,
            dataset.note or ''
        ])
    
    return output.getvalue()


def export_datasets_to_jsonl(datasets: List[Dataset], format_type: str = 'standard') -> str:
    """
    导出数据集为JSONL格式（每行一个JSON对象）
    :param datasets: 数据集列表
    :param format_type: 格式类型
    :return: JSONL字符串
    """
    lines = []
    
    if format_type == 'huggingface':
        for dataset in datasets:
            item = {
                'instruction': dataset.question,
                'input': '',
                'output': dataset.answer
            }
            lines.append(json.dumps(item, ensure_ascii=False))
    elif format_type == 'llamafactory':
        for dataset in datasets:
            item = {
                'instruction': dataset.question,
                'input': '',
                'output': dataset.answer,
                'history': []
            }
            lines.append(json.dumps(item, ensure_ascii=False))
    else:
        for dataset in datasets:
            item = {
                'question': dataset.question,
                'answer': dataset.answer,
                'chunkName': dataset.chunk_name,
                'model': dataset.model,
                'questionLabel': dataset.question_label,
                'cot': dataset.cot or '',
                'confirmed': dataset.confirmed,
                'score': dataset.score,
                'tags': json.loads(dataset.tags) if dataset.tags else [],
                'note': dataset.note or ''
            }
            lines.append(json.dumps(item, ensure_ascii=False))
    
    return '\n'.join(lines)


def get_datasets_for_export(project_id: str, confirmed: Optional[bool] = None, 
                           selected_ids: Optional[List[str]] = None,
                           balance_config: Optional[Dict] = None) -> List[Dataset]:
    """
    获取要导出的数据集
    :param project_id: 项目ID
    :param confirmed: 是否已确认（None表示全部）
    :param selected_ids: 选中的数据集ID列表
    :param balance_config: 平衡配置
    :return: 数据集列表
    """
    queryset = Dataset.objects.filter(project_id=project_id)
    
    # 过滤确认状态
    if confirmed is not None:
        queryset = queryset.filter(confirmed=confirmed)
    
    # 如果指定了选中的ID
    if selected_ids and len(selected_ids) > 0:
        queryset = queryset.filter(id__in=selected_ids)
    
    # 如果指定了平衡配置
    if balance_config:
        # 按标签平衡导出
        tags = balance_config.get('tags', [])
        max_per_tag = balance_config.get('maxPerTag', 100)
        
        balanced_datasets = []
        for tag_label in tags:
            tag_datasets = queryset.filter(
                tags__icontains=tag_label
            )[:max_per_tag]
            balanced_datasets.extend(list(tag_datasets))
        
        return balanced_datasets
    
    return list(queryset)


def get_tag_statistics(project_id: str, confirmed: Optional[bool] = None) -> List[Dict]:
    """
    获取标签统计信息
    :param project_id: 项目ID
    :param confirmed: 是否已确认
    :return: 标签统计列表
    """
    tags = Tag.objects.filter(project_id=project_id)
    stats = []
    
    for tag in tags:
        datasets = Dataset.objects.filter(project_id=project_id)
        
        if confirmed is not None:
            datasets = datasets.filter(confirmed=confirmed)
        
        # 统计包含该标签的数据集数量
        count = datasets.filter(tags__icontains=tag.label).count()
        
        stats.append({
            'id': tag.id,
            'label': tag.label,
            'parentId': tag.parent_id,
            'datasetCount': count
        })
    
    return stats

