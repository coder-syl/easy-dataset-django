"""
单文件 GA 对生成视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from pathlib import Path

from projects.models import Project
from .models import UploadFile, GaPair
from common.response.result import success, error
from .services import generate_ga_pairs


@swagger_auto_schema(
    method='get',
    operation_summary='获取单个文件的GA对',
    responses={200: openapi.Response('GA对列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='为单个文件生成GA对',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'modelConfig': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING),
            'appendMode': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        }
    ),
    responses={200: openapi.Response('生成结果')}
)
@api_view(['GET', 'POST'])
def generate_ga_for_file(request, project_id, file_id):
    """
    GET  获取已有GA对
    POST 为单个文件生成GA对
    """
    try:
        project = get_object_or_404(Project, id=project_id)
        upload_file = get_object_or_404(UploadFile, id=file_id, project=project)
    except Exception:
        return error(message='文件不存在', response_status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        pairs = GaPair.objects.filter(project=project, upload_file=upload_file).order_by('pair_number', 'id')
        data = [{
            'id': str(p.id),
            'pairNumber': p.pair_number,
            'genreTitle': p.genre_title,
            'genreDesc': p.genre_desc,
            'audienceTitle': p.audience_title,
            'audienceDesc': p.audience_desc,
            'isActive': p.is_active,
        } for p in pairs]
        return success(data=data)

    # POST: 生成
    model_config = request.data.get('modelConfig')
    language = request.data.get('language', '中文')
    append_mode = bool(request.data.get('appendMode', False))

    if not model_config:
        return error(message='模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)

    try:
        project_path = Path('local-db') / project_id / 'files'
        file_path = project_path / upload_file.file_name
        if not file_path.exists():
            return error(message='文件不存在', response_status=status.HTTP_404_NOT_FOUND)

        ga_pairs = generate_ga_pairs(
            file_path.read_text(encoding='utf-8', errors='ignore'),
            project_id,
            language,
            model_config
        )

        # 保存到数据库
        saved_pairs = []
        for ga_pair_data in ga_pairs:
            pair = GaPair.objects.create(
                project=project,
                upload_file=upload_file,
                pair_number=min(GaPair.objects.filter(upload_file=upload_file).count() + 1, 5),
                genre_title=ga_pair_data.get('genre') or ga_pair_data.get('genreTitle', ''),
                genre_desc=ga_pair_data.get('genreDesc', ''),
                audience_title=ga_pair_data.get('audience') or ga_pair_data.get('audienceTitle', ''),
                audience_desc=ga_pair_data.get('audienceDesc', ''),
                is_active=True
            )
            saved_pairs.append(pair)

        return success(data={
            'fileId': str(upload_file.id),
            'fileName': upload_file.file_name,
            'gaPairs': [{
                'id': str(p.id),
                'pairNumber': p.pair_number,
                'genreTitle': p.genre_title,
                'genreDesc': p.genre_desc,
                'audienceTitle': p.audience_title,
                'audienceDesc': p.audience_desc,
                'isActive': p.is_active,
            } for p in saved_pairs]
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

