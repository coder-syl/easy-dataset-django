"""
数据集导出服务
支持多种格式：JSON、CSV、JSONL等
"""
import json
import csv
from io import StringIO
from typing import List, Dict, Optional
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


def _get_tag_label_from_id_or_label(project_id: str, tag_id_or_label: str) -> str:
    """
    从标签ID或标签名称获取标签名称
    如果传入的是标签ID，则查询标签表获取标签名称
    如果传入的是标签名称，则直接返回
    :param project_id: 项目ID
    :param tag_id_or_label: 标签ID或标签名称
    :return: 标签名称
    """
    if not tag_id_or_label:
        return ''
    
    # 尝试作为标签ID查询
    try:
        tag = Tag.objects.filter(id=tag_id_or_label, project_id=project_id).first()
        if tag:
            return tag.label
    except:
        pass
    
    # 如果不是标签ID，则假设是标签名称，直接返回
    return tag_id_or_label


def get_datasets_for_export(project_id: str, confirmed: Optional[bool] = None, 
                           selected_ids: Optional[List[str]] = None,
                           balance_config: Optional[List[Dict]] = None) -> List[Dataset]:
    """
    获取要导出的数据集
    :param project_id: 项目ID
    :param confirmed: 是否已确认（None表示全部）
    :param selected_ids: 选中的数据集ID列表
    :param balance_config: 平衡配置，格式为 [{tagLabel: str, maxCount: int}] 或 [{tagId: str, maxCount: int}]
    :return: 数据集列表
    """
    queryset = Dataset.objects.filter(project_id=project_id)
    
    # 过滤确认状态
    if confirmed is not None:
        queryset = queryset.filter(confirmed=confirmed)
    
    # 如果指定了选中的ID
    if selected_ids and len(selected_ids) > 0:
        queryset = queryset.filter(id__in=selected_ids)
    
    # 如果指定了平衡配置（数组格式，与Node.js一致）
    if balance_config and isinstance(balance_config, list):
        balanced_datasets = []
        for config in balance_config:
            # 支持 tagLabel 或 tagId（兼容两种情况）
            tag_label = config.get('tagLabel', '') or config.get('tagId', '')
            max_count = config.get('maxCount', 100)
            
            # 如果是标签ID，转换为标签名称
            tag_label = _get_tag_label_from_id_or_label(project_id, tag_label)
            
            if not tag_label:
                continue
            
            # 使用 questionLabel 字段精确匹配（与Node.js一致）
            tag_datasets = queryset.filter(
                question_label=tag_label
            ).order_by('-create_at')[:max_count]
            balanced_datasets.extend(list(tag_datasets))
        
        return balanced_datasets
    
    return list(queryset.order_by('-create_at'))


def get_datasets_batch(project_id: str, confirmed: Optional[bool] = None,
                      offset: int = 0, batch_size: int = 1000) -> Dict:
    """
    分批获取数据集（用于大数据量导出）
    :param project_id: 项目ID
    :param confirmed: 是否已确认（None表示全部）
    :param offset: 偏移量
    :param batch_size: 批次大小
    :return: 包含 data 和 hasMore 的字典
    """
    queryset = Dataset.objects.filter(project_id=project_id)
    
    if confirmed is not None:
        queryset = queryset.filter(confirmed=confirmed)
    
    total_count = queryset.count()
    datasets = list(queryset.order_by('-create_at')[offset:offset + batch_size])
    has_more = offset + len(datasets) < total_count
    
    return {
        'data': datasets,
        'hasMore': has_more
    }


def get_datasets_by_ids(project_id: str, dataset_ids: List[str]) -> List[Dataset]:
    """
    根据数据集ID列表获取数据集
    :param project_id: 项目ID
    :param dataset_ids: 数据集ID列表
    :return: 数据集列表
    """
    if not dataset_ids:
        return []
    
    return list(Dataset.objects.filter(
        project_id=project_id,
        id__in=dataset_ids
    ).order_by('-create_at'))


def get_datasets_by_ids_batch(project_id: str, dataset_ids: List[str],
                             offset: int = 0, batch_size: int = 1000) -> Dict:
    """
    根据数据集ID列表分批获取数据集
    :param project_id: 项目ID
    :param dataset_ids: 数据集ID列表
    :param offset: 偏移量
    :param batch_size: 批次大小
    :return: 包含 data 和 hasMore 的字典
    """
    if not dataset_ids:
        return {'data': [], 'hasMore': False}
    
    queryset = Dataset.objects.filter(
        project_id=project_id,
        id__in=dataset_ids
    )
    
    total_count = queryset.count()
    datasets = list(queryset.order_by('-create_at')[offset:offset + batch_size])
    has_more = offset + len(datasets) < total_count
    
    return {
        'data': datasets,
        'hasMore': has_more
    }


def get_balanced_datasets_by_tags_batch(project_id: str, balance_config: List[Dict],
                                       confirmed: Optional[bool] = None,
                                       offset: int = 0, batch_size: int = 1000) -> Dict:
    """
    分批获取按标签平衡的数据集（用于大数据量导出）
    :param project_id: 项目ID
    :param balance_config: 平衡配置，格式为 [{tagLabel: str, maxCount: int}] 或 [{tagId: str, maxCount: int}]
    :param confirmed: 是否已确认（None表示全部）
    :param offset: 偏移量
    :param batch_size: 批次大小
    :return: 包含 data 和 hasMore 的字典
    """
    # 首先获取所有符合条件的数据集ID（用于分页）
    all_results = []
    
    queryset = Dataset.objects.filter(project_id=project_id)
    if confirmed is not None:
        queryset = queryset.filter(confirmed=confirmed)
    
    for config in balance_config:
        # 支持 tagLabel 或 tagId（兼容两种情况）
        tag_label = config.get('tagLabel', '') or config.get('tagId', '')
        max_count = config.get('maxCount', 100)
        
        # 规范化 maxCount
        count = int(max_count) if isinstance(max_count, (int, str)) and str(max_count).isdigit() else 0
        if count <= 0:
            continue
        
        # 如果是标签ID，转换为标签名称
        tag_label = _get_tag_label_from_id_or_label(project_id, tag_label)
        
        if not tag_label:
            continue
        
        # 获取该标签下的数据集ID（使用 questionLabel 字段）
        tag_datasets = queryset.filter(
            question_label=tag_label
        ).order_by('-create_at')[:count].values('id', 'create_at')
        
        all_results.extend(list(tag_datasets))
    
    # 按创建时间排序
    all_results.sort(key=lambda x: x['create_at'], reverse=True)
    
    # 分页获取当前批次的ID
    batch_ids = [item['id'] for item in all_results[offset:offset + batch_size]]
    
    if not batch_ids:
        return {'data': [], 'hasMore': False}
    
    # 根据ID获取完整数据
    batch_data = list(Dataset.objects.filter(
        project_id=project_id,
        id__in=batch_ids
    ))
    
    has_more = offset + batch_size < len(all_results)
    
    return {
        'data': batch_data,
        'hasMore': has_more
    }


def get_tag_statistics(project_id: str, confirmed: Optional[bool] = None) -> List[Dict]:
    """
    获取标签统计信息（使用 questionLabel 字段统计，与Node.js一致）
    :param project_id: 项目ID
    :param confirmed: 是否已确认
    :return: 标签统计列表，格式为 [{tagLabel: str, datasetCount: int}]
    """
    from django.db.models import Count
    
    queryset = Dataset.objects.filter(project_id=project_id)
    
    if confirmed is not None:
        queryset = queryset.filter(confirmed=confirmed)
    
    # 使用 questionLabel 字段分组统计（与Node.js一致）
    tag_counts = queryset.values('question_label').annotate(
        dataset_count=Count('id')
    ).order_by('question_label')
    
    stats = []
    for item in tag_counts:
        tag_label = item['question_label'] or ''
        if tag_label:  # 只返回有标签的统计
            stats.append({
                'tagLabel': tag_label,
                'datasetCount': item['dataset_count']
            })
    
    return stats

