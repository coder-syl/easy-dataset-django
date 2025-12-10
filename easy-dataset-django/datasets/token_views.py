"""
数据集 Token 统计与标签统计视图
"""
import json
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from projects.models import Project
from .models import Dataset
from common.response.result import success, error


def _count_tokens(text: str) -> int:
    """简单的token计数（按空格分词近似代替）。"""
    if not text:
        return 0
    return len(text.split())


@swagger_auto_schema(
    method='get',
    operation_summary='获取数据集Token统计',
    responses={200: openapi.Response('Token统计')}
)
@api_view(['GET'])
def dataset_token_count(request, project_id, dataset_id):
    """获取单个数据集的token计数（问题+答案+cOT）"""
    try:
        project = get_object_or_404(Project, id=project_id)
        dataset = get_object_or_404(Dataset, id=dataset_id, project=project)
    except Exception:
        return error(message='数据集不存在', response_status=status.HTTP_404_NOT_FOUND)

    try:
        total_tokens = _count_tokens(dataset.question) + _count_tokens(dataset.answer) + _count_tokens(dataset.cot or '')
        return success(data={
            'datasetId': str(dataset.id),
            'questionTokens': _count_tokens(dataset.question),
            'answerTokens': _count_tokens(dataset.answer),
            'cotTokens': _count_tokens(dataset.cot or ''),
            'totalTokens': total_tokens
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取数据集标签统计',
    responses={200: openapi.Response('标签统计')}
)
@api_view(['GET'])
def dataset_tags(request, project_id):
    """统计数据集标签出现次数"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)

    try:
        datasets = Dataset.objects.filter(project=project)
        tag_counter = {}
        for ds in datasets:
            tags_str = ds.tags or ''
            tags_list = []
            try:
                tags_list = json.loads(tags_str) if tags_str else []
            except Exception:
                # 如果不是json，按逗号拆
                tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]
            for t in tags_list:
                tag_counter[t] = tag_counter.get(t, 0) + 1
        stats = [{'tag': k, 'count': v} for k, v in tag_counter.items()]
        return success(data={'tags': stats})
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

