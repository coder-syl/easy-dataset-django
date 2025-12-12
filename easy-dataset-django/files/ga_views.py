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
from llm.models import ModelConfig


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
@swagger_auto_schema(
    method='put',
    operation_summary='覆盖/追加指定文件的GA对',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'gaPairs': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'genreTitle': openapi.Schema(type=openapi.TYPE_STRING),
                        'genreDesc': openapi.Schema(type=openapi.TYPE_STRING),
                        'audienceTitle': openapi.Schema(type=openapi.TYPE_STRING),
                        'audienceDesc': openapi.Schema(type=openapi.TYPE_STRING),
                        'isActive': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            ),
            'appendMode': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
        }
    ),
    responses={200: openapi.Response('保存结果')}
)
@swagger_auto_schema(
    method='patch',
    operation_summary='更新单个GA对的激活状态',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'pairId': openapi.Schema(type=openapi.TYPE_STRING),
            'isActive': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        },
        required=['pairId', 'isActive']
    ),
    responses={200: openapi.Response('更新结果')}
)
@api_view(['GET', 'POST', 'PUT', 'PATCH'])
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

    if request.method == 'PATCH':
        pair_id = request.data.get('pairId')
        is_active = request.data.get('isActive')
        if pair_id is None or is_active is None:
            return error(message='pairId 和 isActive 为必填', response_status=status.HTTP_400_BAD_REQUEST)
        try:
            pair = GaPair.objects.get(id=pair_id, project=project, upload_file=upload_file)
            pair.is_active = bool(is_active)
            pair.save(update_fields=['is_active', 'update_at'])
            return success(data={
                'id': str(pair.id),
                'pairNumber': pair.pair_number,
                'isActive': pair.is_active
            })
        except GaPair.DoesNotExist:
            return error(message='GA对不存在', response_status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if request.method == 'PUT':
        ga_pairs = request.data.get('gaPairs', [])
        append_mode = bool(request.data.get('appendMode', False))
        if not isinstance(ga_pairs, list):
            return error(message='gaPairs 必须是数组', response_status=status.HTTP_400_BAD_REQUEST)
        try:
            existing_count = GaPair.objects.filter(project=project, upload_file=upload_file).count()
            start_number = existing_count + 1 if append_mode else 1
            if not append_mode:
                GaPair.objects.filter(project=project, upload_file=upload_file).delete()
            to_create = []
            for idx, p in enumerate(ga_pairs):
                genre = p.get('genre') or {}
                audience = p.get('audience') or {}
                genre_title = genre.get('title') or p.get('genreTitle', '') or p.get('genre', '')
                genre_desc = genre.get('description') or p.get('genreDesc', '')
                audience_title = audience.get('title') or p.get('audienceTitle', '') or p.get('audience', '')
                audience_desc = audience.get('description') or p.get('audienceDesc', '')
                to_create.append(GaPair(
                    project=project,
                    upload_file=upload_file,
                    pair_number=start_number + idx,
                    genre_title=genre_title,
                    genre_desc=genre_desc,
                    audience_title=audience_title,
                    audience_desc=audience_desc,
                    is_active=bool(p.get('isActive', True))
                ))
            GaPair.objects.bulk_create(to_create)
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
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # POST: 生成
    model_config = request.data.get('modelConfig')
    language = request.data.get('language', '中文')
    append_mode = bool(request.data.get('appendMode', False))

    if not model_config:
        # 兼容 Node 逻辑：自动选取项目的启用模型（优先 default_model_config_id，其次首个 status=1）
        active_config = None
        try:
            if project.default_model_config_id:
                active_config = ModelConfig.objects.filter(id=project.default_model_config_id, project=project, status=1).first()
            if not active_config:
                active_config = ModelConfig.objects.filter(project=project, status=1).order_by('-update_at').first()
        except Exception:
            active_config = None

        if not active_config:
            # 再次回退：如果没有启用的模型，取项目下任意一条最新配置尝试调用（与 Node 无模型时的兜底区别在于尽量不阻断）
            try:
                active_config = ModelConfig.objects.filter(project=project).order_by('-update_at').first()
            except Exception:
                active_config = None

        if not active_config:
            return error(message='未找到启用的模型配置，请先在模型配置中启用模型', response_status=status.HTTP_400_BAD_REQUEST)

        model_config = {
            'provider_id': active_config.provider_id,
            'provider_name': active_config.provider_name,
            'endpoint': active_config.endpoint,
            'api_key': active_config.api_key,
            'model_id': active_config.model_id,
            'model_name': active_config.model_name,
            'temperature': active_config.temperature,
            'max_tokens': active_config.max_tokens,
            'top_p': active_config.top_p,
            'top_k': active_config.top_k
        }

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
        existing_count = GaPair.objects.filter(upload_file=upload_file).count()
        for idx, ga_pair_data in enumerate(ga_pairs):
            genre = ga_pair_data.get('genre') or {}
            audience = ga_pair_data.get('audience') or {}
            genre_title = genre.get('title') or ga_pair_data.get('genreTitle', '') or ga_pair_data.get('genre', '')
            genre_desc = genre.get('description') or ga_pair_data.get('genreDesc', '')
            audience_title = audience.get('title') or ga_pair_data.get('audienceTitle', '') or ga_pair_data.get('audience', '')
            audience_desc = audience.get('description') or ga_pair_data.get('audienceDesc', '')
            pair = GaPair.objects.create(
                project=project,
                upload_file=upload_file,
                pair_number=existing_count + idx + 1,
                genre_title=genre_title,
                genre_desc=genre_desc,
                audience_title=audience_title,
                audience_desc=audience_desc,
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

