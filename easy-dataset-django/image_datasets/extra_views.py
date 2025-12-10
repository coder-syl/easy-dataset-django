"""
图像数据集导出与标签统计占位
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import json
import io
import zipfile

from projects.models import Project
from .models import ImageDataset
from common.response.result import success, error


def _serialize_image_dataset(ds: ImageDataset):
    return {
        'id': str(ds.id),
        'projectId': str(ds.project_id),
        'imageId': ds.image_id,
        'imageName': ds.image_name,
        'question': ds.question,
        'answer': ds.answer,
        'cot': ds.cot,
        'confirmed': ds.confirmed,
        'score': ds.score,
        'tags': ds.tags,
        'note': ds.note,
    }


@swagger_auto_schema(
    method='post',
    operation_summary='导出图像数据集',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'format': openapi.Schema(type=openapi.TYPE_STRING, description='json|jsonl', default='json'),
            'confirmed': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'selectedIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
        }
    )
)
@api_view(['POST'])
def export_image_datasets(request, project_id):
    """导出图像数据集为 JSON/JSONL"""
    try:
        get_object_or_404(Project, id=project_id)
        fmt = request.data.get('format', 'json')
        confirmed = request.data.get('confirmed')
        selected_ids = request.data.get('selectedIds') or []

        queryset = ImageDataset.objects.filter(project_id=project_id)
        if confirmed is not None:
            queryset = queryset.filter(confirmed=bool(confirmed))
        if selected_ids:
            queryset = queryset.filter(id__in=selected_ids)

        data_list = [_serialize_image_dataset(ds) for ds in queryset]

        if fmt == 'jsonl':
            content = '\n'.join(json.dumps(item, ensure_ascii=False) for item in data_list)
            resp = HttpResponse(content, content_type='text/plain; charset=utf-8')
            resp['Content-Disposition'] = 'attachment; filename="image-datasets.jsonl"'
            return resp
        else:
            content = json.dumps(data_list, ensure_ascii=False, indent=2)
            resp = HttpResponse(content, content_type='application/json; charset=utf-8')
            resp['Content-Disposition'] = 'attachment; filename="image-datasets.json"'
            return resp
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(method='get', operation_summary='导出图像数据集ZIP')
@api_view(['GET'])
def export_image_datasets_zip(request, project_id):
    """导出图像数据集为zip（包含json）"""
    try:
        get_object_or_404(Project, id=project_id)
        datasets = [_serialize_image_dataset(ds) for ds in ImageDataset.objects.filter(project_id=project_id)]
        memfile = io.BytesIO()
        with zipfile.ZipFile(memfile, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('image-datasets.json', json.dumps(datasets, ensure_ascii=False, indent=2))
        memfile.seek(0)
        resp = HttpResponse(memfile.read(), content_type='application/zip')
        resp['Content-Disposition'] = 'attachment; filename="image-datasets.zip"'
        return resp
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(method='get', operation_summary='获取图像数据集标签统计')
@api_view(['GET'])
def image_dataset_tags(request, project_id):
    try:
        get_object_or_404(Project, id=project_id)
        tag_counter = {}
        for ds in ImageDataset.objects.filter(project_id=project_id):
            tags_str = ds.tags or ''
            tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []
            for t in tags:
                tag_counter[t] = tag_counter.get(t, 0) + 1
        stats = [{'tag': k, 'count': v} for k, v in tag_counter.items()]
        return success(data={'tags': stats})
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

