"""
项目管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from .models import Project
from .serializers import ProjectSerializer, ProjectCreateSerializer
from llm.models import ModelConfig
from common.response.result import success, error
from django.http import HttpResponse
import json
from django.db.models import Max

# import dataset models for counts/exports
from datasets.models import Dataset
from conversations.models import DatasetConversation
from images.models import ImageDataset

def _serialize_dataset_simple(ds: Dataset):
    return {
        'id': ds.id,
        'type': 'single',
        'question': ds.question,
        'answer': ds.answer,
        'tags': json.loads(ds.tags) if ds.tags else [],
        'confirmed': ds.confirmed,
        'createAt': ds.create_at.isoformat() if hasattr(ds.create_at, 'isoformat') else str(ds.create_at)
    }

def _serialize_conversation_simple(conv: DatasetConversation):
    # return basic shape for multi-turn
    try:
        messages = json.loads(conv.raw_messages) if conv.raw_messages else []
    except Exception:
        messages = []
    return {
        'id': conv.id,
        'type': 'multi',
        'question': conv.question,
        'messages': messages,
        'tags': conv.tags,
        'confirmed': conv.confirmed,
        'createAt': conv.create_at.isoformat() if hasattr(conv.create_at, 'isoformat') else str(conv.create_at)
    }

def _serialize_image_simple(imgds: ImageDataset):
    return {
        'id': imgds.id,
        'type': 'image',
        'image_name': imgds.image_name,
        'question': imgds.question,
        'answer': imgds.answer,
        'tags': imgds.tags,
        'confirmed': imgds.confirmed,
        'createAt': imgds.create_at.isoformat() if hasattr(imgds.create_at, 'isoformat') else str(imgds.create_at)
    }


@swagger_auto_schema(
    method='get',
    operation_summary='获取项目下三类数据集的总览统计（单轮/多轮/图片）'
)
@api_view(['GET'])
def datasets_overview(request, project_id):
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    try:
        single_count = Dataset.objects.filter(project=project).count()
        multi_count = DatasetConversation.objects.filter(project=project).count()
        image_count = ImageDataset.objects.filter(project=project).count()

        # last updated across models
        last_single = Dataset.objects.filter(project=project).aggregate(Max('update_at'))['update_at__max']
        last_multi = DatasetConversation.objects.filter(project=project).aggregate(Max('update_at'))['update_at__max']
        last_image = ImageDataset.objects.filter(project=project).aggregate(Max('update_at'))['update_at__max']
        last_updated = max(filter(None, [last_single, last_multi, last_image])) if any([last_single, last_multi, last_image]) else None

        # sample latest of each
        sample_single = Dataset.objects.filter(project=project).order_by('-create_at').first()
        sample_multi = DatasetConversation.objects.filter(project=project).order_by('-create_at').first()
        sample_image = ImageDataset.objects.filter(project=project).order_by('-create_at').first()

        result = {
            'counts': {
                'single': single_count,
                'multi': multi_count,
                'image': image_count
            },
            'lastUpdated': last_updated.isoformat() if hasattr(last_updated, 'isoformat') else (str(last_updated) if last_updated else None),
            'samples': {
                'single': _serialize_dataset_simple(sample_single) if sample_single else None,
                'multi': _serialize_conversation_simple(sample_multi) if sample_multi else None,
                'image': _serialize_image_simple(sample_image) if sample_image else None
            }
        }
        return success(data=result)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='同步导出所选类型的数据集（single/multi/image）为 JSONL/JSON/CSV'
)
@api_view(['POST'])
def export_all_datasets(request, project_id):
    """合并导出三类数据集的同步实现（默认 jsonl）"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    try:
        body = request.data if hasattr(request, 'data') else {}
        types = body.get('types', ['single', 'multi', 'image'])
        export_format = body.get('format', 'jsonl')  # json/jsonl/csv
        confirmed_only = body.get('confirmed', None)
        selected_ids = body.get('selectedIds', {})  # optional dict: {single:[], multi:[], image:[]}

        exported = []

        if 'single' in types:
            qs = Dataset.objects.filter(project=project)
            if confirmed_only is not None:
                qs = qs.filter(confirmed=bool(confirmed_only))
            ids = selected_ids.get('single') if isinstance(selected_ids, dict) else None
            if ids:
                qs = qs.filter(id__in=ids)
            for d in qs:
                exported.append(_serialize_dataset_simple(d))

        if 'multi' in types:
            qs = DatasetConversation.objects.filter(project=project)
            if confirmed_only is not None:
                qs = qs.filter(confirmed=bool(confirmed_only))
            ids = selected_ids.get('multi') if isinstance(selected_ids, dict) else None
            if ids:
                qs = qs.filter(id__in=ids)

            # multi-turn needs special handling: support formatType (sharegpt/chatml/alpaca/raw)
            format_type = body.get('formatType', 'raw')  # sharegpt/chatml/alpaca/raw
            payload = []
            for c in qs:
                try:
                    messages = json.loads(c.raw_messages) if c.raw_messages else []
                except Exception:
                    messages = []
                payload.append({
                    'id': c.id,
                    'questionId': c.question_id,
                    'question': c.question,
                    'chunkId': c.chunk_id,
                    'model': c.model,
                    'scenario': c.scenario,
                    'roleA': c.role_a,
                    'roleB': c.role_b,
                    'turnCount': c.turn_count,
                    'maxTurns': c.max_turns,
                    'tags': c.tags,
                    'score': c.score,
                    'aiEvaluation': c.ai_evaluation,
                    'confirmed': c.confirmed,
                    'messages': messages
                })

            # helper to map roles
            def map_role(msg_role, conv_item):
                try:
                    if conv_item.get('roleA') and msg_role == conv_item.get('roleA'):
                        return 'user'
                    if conv_item.get('roleB') and msg_role == conv_item.get('roleB'):
                        return 'assistant'
                except Exception:
                    pass
                lower = (msg_role or '').lower()
                if 'user' in lower:
                    return 'user'
                if 'assistant' in lower:
                    return 'assistant'
                return msg_role

            exported_multi = []
            if format_type == 'sharegpt':
                for item in payload:
                    conv_msgs = []
                    for m in item.get('messages', []):
                        role = map_role(m.get('role'), item)
                        from_field = 'system' if role == 'system' else ('user' if 'user' in (role or '').lower() else ('assistant' if 'assistant' in (role or '').lower() else role))
                        conv_msgs.append({'from': from_field, 'value': m.get('content')})
                    exported_multi.append({
                        'id': item.get('id'),
                        'conversations': conv_msgs,
                        'meta': {
                            'questionId': item.get('questionId'),
                            'question': item.get('question'),
                            'model': item.get('model'),
                            'scenario': item.get('scenario'),
                            'tags': item.get('tags'),
                            'score': item.get('score'),
                            'confirmed': item.get('confirmed')
                        }
                    })
            elif format_type == 'chatml':
                for item in payload:
                    msgs = []
                    for m in item.get('messages', []):
                        role = map_role(m.get('role'), item)
                        msgs.append({'role': role, 'content': m.get('content')})
                    exported_multi.append({
                        'id': item.get('id'),
                        'messages': msgs,
                        'meta': {
                            'questionId': item.get('questionId'),
                            'question': item.get('question'),
                            'model': item.get('model'),
                            'scenario': item.get('scenario'),
                            'tags': item.get('tags'),
                            'score': item.get('score'),
                            'confirmed': item.get('confirmed')
                        }
                    })
            elif format_type == 'alpaca':
                for item in payload:
                    msgs = item.get('messages', []) or []
                    norm_msgs = []
                    for m in msgs:
                        try:
                            role = map_role(m.get('role'), item)
                        except Exception:
                            role = (m.get('role') or '')
                        norm_msgs.append({'role': role, 'content': m.get('content')})
                    item_pairs = []
                    for i in range(1, len(norm_msgs)):
                        prev = norm_msgs[i-1]
                        cur = norm_msgs[i]
                        prev_role = (prev.get('role') or '').lower()
                        cur_role = (cur.get('role') or '').lower()
                        if 'user' in prev_role and 'assistant' in cur_role:
                            item_pairs.append((prev, cur))
                    if not item_pairs and len(norm_msgs) >= 2:
                        for i in range(1, len(norm_msgs)):
                            prev = norm_msgs[i-1]
                            cur = norm_msgs[i]
                            if prev.get('content') or cur.get('content'):
                                item_pairs.append((prev, cur))
                    if not item_pairs and len(norm_msgs) == 1:
                        single = norm_msgs[0]
                        exported_multi.append({
                            'instruction': single.get('content') or '',
                            'input': '',
                            'output': '',
                            'meta': {'conversationId': item.get('id')}
                        })
                    else:
                        for prev, cur in item_pairs:
                            exported_multi.append({
                                'instruction': prev.get('content') or '',
                                'input': '',
                                'output': cur.get('content') or '',
                                'meta': {'conversationId': item.get('id')}
                            })
            else:
                # raw: include normalized messages
                for item in payload:
                    msgs = []
                    for m in item.get('messages', []):
                        role = map_role(m.get('role'), item)
                        msgs.append({'role': role, 'content': m.get('content')})
                    exported_multi.append({
                        'id': item.get('id'),
                        'messages': msgs,
                        'meta': {
                            'questionId': item.get('questionId'),
                            'question': item.get('question'),
                            'model': item.get('model'),
                            'scenario': item.get('scenario'),
                            'tags': item.get('tags'),
                            'score': item.get('score'),
                            'confirmed': item.get('confirmed')
                        }
                    })

            # merge multi exported into overall exported list
            exported.extend(exported_multi)

        if 'image' in types:
            qs = ImageDataset.objects.filter(project=project)
            if confirmed_only is not None:
                qs = qs.filter(confirmed=bool(confirmed_only))
            ids = selected_ids.get('image') if isinstance(selected_ids, dict) else None
            if ids:
                qs = qs.filter(id__in=ids)
            for img in qs:
                exported.append(_serialize_image_simple(img))

        # If client requested a concrete file format, render according to format on server (download)
        request_format = body.get('format')
        if request_format:
            export_format = request_format
        else:
            export_format = None

        # render according to format (server-side)
        if export_format == 'jsonl':
            lines = [json.dumps(it, ensure_ascii=False) for it in exported]
            text = '\n'.join(lines)
            resp = HttpResponse(text, content_type='text/plain; charset=utf-8')
            resp['Content-Disposition'] = 'attachment; filename="datasets_export.jsonl"'
            return resp
        elif export_format == 'csv':
            # simple CSV flatten by keys of first item
            import io, csv as _csv
            output = io.StringIO()
            if exported:
                headers = list(exported[0].keys())
                writer = _csv.DictWriter(output, fieldnames=headers)
                writer.writeheader()
                for it in exported:
                    row = {}
                    for h in headers:
                        val = it.get(h, '')
                        if isinstance(val, (list, dict)):
                            val = json.dumps(val, ensure_ascii=False)
                        row[h] = val
                    writer.writerow(row)
            text = output.getvalue()
            resp = HttpResponse(text, content_type='text/csv; charset=utf-8')
            resp['Content-Disposition'] = 'attachment; filename="datasets_export.csv"'
            return resp
        else:
            # If no export_format requested, return JSON data (wrapped) so frontend can format client-side
            return success(data=exported)
    except Exception as e:
        return error(message=f'导出失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@swagger_auto_schema(
    method='get',
    operation_summary='获取项目列表',
    responses={200: openapi.Response('项目列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='创建项目',
    request_body=ProjectCreateSerializer,
    responses={201: openapi.Response('创建成功')}
)
@api_view(['GET', 'POST'])
def project_list_create(request):
    """获取项目列表或创建项目"""
    if request.method == 'GET':
        try:
            # 使用 prefetch_related 优化查询，避免 N+1 问题
            projects = Project.objects.prefetch_related('questions', 'datasets').all().order_by('-create_at')
            serializer = ProjectSerializer(projects, many=True)
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            serializer = ProjectCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            # 验证项目名称是否已存在
            name = serializer.validated_data.get('name')
            if Project.objects.filter(name=name).exists():
                return error(message='项目名称已存在', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 创建项目
            project = serializer.save()
            
            # 如果指定了要复用的项目配置
            reuse_config_from = request.data.get('reuseConfigFrom')
            if reuse_config_from:
                try:
                    source_configs = ModelConfig.objects.filter(project_id=reuse_config_from)
                    new_configs = []
                    for config in source_configs:
                        new_config = ModelConfig(
                            project=project,
                            provider_id=config.provider_id,
                            provider_name=config.provider_name,
                            endpoint=config.endpoint,
                            api_key=config.api_key,
                            model_id=config.model_id,
                            model_name=config.model_name,
                            type=config.type,
                            temperature=config.temperature,
                            max_tokens=config.max_tokens,
                            top_p=config.top_p,
                            top_k=config.top_k,
                            status=config.status
                        )
                        new_configs.append(new_config)
                    ModelConfig.objects.bulk_create(new_configs)
                except Exception as e:
                    # 配置复制失败不影响项目创建
                    pass
            
            result_serializer = ProjectSerializer(project)
            return success(data=result_serializer.data, response_status=status.HTTP_201_CREATED)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取项目详情',
    responses={200: openapi.Response('项目详情')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新项目',
    request_body=ProjectSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除项目',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'PUT', 'DELETE'])
def project_detail_update_delete(request, project_id):
    """获取、更新或删除项目"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            serializer = ProjectSerializer(project)
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            print(f"[Django] Updating project {project_id} with data: {request.data}")
            serializer = ProjectSerializer(project, data=request.data, partial=True)
            if not serializer.is_valid():
                print(f"[Django] Serializer validation failed: {serializer.errors}")
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            updated_project = serializer.save()
            print(f"[Django] Project updated successfully. default_model_config_id: {updated_project.default_model_config_id}")
            return success(data=serializer.data)
        except Exception as e:
            print(f"[Django] Error updating project: {str(e)}")
            import traceback
            traceback.print_exc()
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            project.delete()
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
