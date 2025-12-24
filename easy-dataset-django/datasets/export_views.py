"""
数据集导出/导入视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import json

from projects.models import Project
from .export_service import (
    get_datasets_for_export,
    get_tag_statistics,
    get_datasets_batch,
    get_datasets_by_ids,
    get_datasets_by_ids_batch,
    get_balanced_datasets_by_tags_batch
)
from common.response.result import success, error


def serialize_dataset(dataset):
    """
    序列化数据集为驼峰格式（与Node.js一致）
    """
    return {
        'id': dataset.id,
        'question': dataset.question,
        'answer': dataset.answer,
        'cot': dataset.cot or '',
        'questionLabel': dataset.question_label or '',
        'chunkName': dataset.chunk_name or '',
        'chunkContent': getattr(dataset, 'chunk_content', '') or '',
        'model': dataset.model or '',
        'confirmed': dataset.confirmed,
        'score': dataset.score,
        'tags': json.loads(dataset.tags) if dataset.tags else [],
        'note': dataset.note or '',
        'other': json.loads(dataset.other) if dataset.other else {},
        'createAt': dataset.create_at.isoformat() if hasattr(dataset.create_at, 'isoformat') else str(dataset.create_at),
        'updateAt': dataset.update_at.isoformat() if hasattr(dataset.update_at, 'isoformat') else str(dataset.update_at)
    }


@swagger_auto_schema(
    method='get',
    operation_summary='获取标签统计信息',
    responses={200: openapi.Response('标签统计')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='导出数据集',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'selectedIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'balanceConfig': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
            'balanceMode': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'batchMode': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'offset': openapi.Schema(type=openapi.TYPE_INTEGER),
            'batchSize': openapi.Schema(type=openapi.TYPE_INTEGER),
            'status': openapi.Schema(type=openapi.TYPE_STRING),
            'format': openapi.Schema(type=openapi.TYPE_STRING),
            'exportFormat': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('导出成功')}
)
@api_view(['GET', 'POST'])
def dataset_export(request, project_id):
    """导出数据集或获取标签统计"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # 获取标签统计信息
        try:
            confirmed_param = request.GET.get('confirmed')
            confirmed = None if confirmed_param is None else (confirmed_param.lower() == 'true')
            
            stats = get_tag_statistics(project_id, confirmed=confirmed)
            # 与 Node.js 一致：直接返回数组，不使用 success() 包装
            from rest_framework.response import Response
            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        # 导出数据集
        try:
            # 获取请求体
            body = request.data if hasattr(request, 'data') else {}
            
            # 统一状态参数处理（支持 status 和 confirmed，与Node.js一致）
            status_param = body.get('status')
            confirmed = None
            if status_param == 'confirmed':
                confirmed = True
            elif status_param == 'unconfirmed':
                confirmed = False
            
            # 检查是否是分批导出模式
            batch_mode = body.get('batchMode', False)
            offset = body.get('offset', 0)
            batch_size = body.get('batchSize', 1000)
            
            # 检查是否是平衡导出
            balance_mode = body.get('balanceMode', False)
            balance_config = body.get('balanceConfig')
            
            # 检查是否有选中的数据集ID
            selected_ids = body.get('selectedIds')
            
            if batch_mode:
                # 分批导出模式（返回JSON数据，与Node.js一致）
                if selected_ids and len(selected_ids) > 0:
                    # 按选中ID分批导出
                    result = get_datasets_by_ids_batch(project_id, selected_ids, offset, batch_size)
                    datasets = result['data']
                    has_more = result['hasMore']
                    return success(data={
                        'data': [serialize_dataset(d) for d in datasets],
                        'hasMore': has_more,
                        'offset': offset + len(datasets)
                    })
                elif balance_mode and balance_config:
                    # 平衡分批导出
                    parsed_config = balance_config if isinstance(balance_config, list) else json.loads(balance_config) if isinstance(balance_config, str) else []
                    result = get_balanced_datasets_by_tags_batch(project_id, parsed_config, confirmed, offset, batch_size)
                    datasets = result['data']
                    has_more = result['hasMore']
                    return success(data={
                        'data': [serialize_dataset(d) for d in datasets],
                        'hasMore': has_more,
                        'offset': offset + len(datasets)
                    })
                else:
                    # 常规分批导出
                    result = get_datasets_batch(project_id, confirmed, offset, batch_size)
                    datasets = result['data']
                    has_more = result['hasMore']
                    return success(data={
                        'data': [serialize_dataset(d) for d in datasets],
                        'hasMore': has_more,
                        'offset': offset + len(datasets)
                    })
            else:
                # 传统一次性导出模式（保持向后兼容，返回JSON数据）
                if selected_ids and len(selected_ids) > 0:
                    # 按选中ID导出
                    datasets = get_datasets_by_ids(project_id, selected_ids)
                elif balance_mode and balance_config:
                    # 平衡导出模式
                    parsed_config = balance_config if isinstance(balance_config, list) else json.loads(balance_config) if isinstance(balance_config, str) else []
                    datasets = get_datasets_for_export(project_id, confirmed=confirmed, balance_config=parsed_config)
                else:
                    # 常规导出模式
                    datasets = get_datasets_for_export(project_id, confirmed=confirmed)
                
                # 序列化数据集（返回驼峰格式，与Node.js一致）
                serialized_data = [serialize_dataset(d) for d in datasets]
                # 如果请求指定了导出格式（json/jsonl/csv），返回文本内容以供下载
                request_format = body.get('format')
                if request_format:
                    if request_format == 'jsonl':
                        text = '\n'.join(json.dumps(item, ensure_ascii=False) for item in serialized_data)
                    elif request_format == 'csv':
                        # build CSV with headers from keys of first item
                        import io, csv as _csv
                        output = io.StringIO()
                        if serialized_data:
                            headers = list(serialized_data[0].keys())
                            writer = _csv.DictWriter(output, fieldnames=headers)
                            writer.writeheader()
                            for it in serialized_data:
                                row = {}
                                for h in headers:
                                    val = it.get(h, '')
                                    if isinstance(val, (list, dict)):
                                        val = json.dumps(val, ensure_ascii=False)
                                    row[h] = val
                                writer.writerow(row)
                        text = output.getvalue()
                    else:
                        text = json.dumps(serialized_data, ensure_ascii=False, indent=2)

                    return success(data={
                        'success': True,
                        'format': request_format,
                        'count': len(serialized_data),
                        'content': text
                    })

                return success(data=serialized_data)
        except Exception as e:
            return error(message=f'导出失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='导入数据集',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'datasets': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT)
            ),
            'sourceInfo': openapi.Schema(type=openapi.TYPE_OBJECT)
        }
    ),
    responses={200: openapi.Response('导入成功')}
)
@api_view(['POST'])
def dataset_import(request, project_id):
    """导入数据集"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    try:
        datasets_data = request.data.get('datasets', [])
        source_info = request.data.get('sourceInfo', {})
        
        if not datasets_data or not isinstance(datasets_data, list):
            return error(message='数据集数据格式错误', response_status=status.HTTP_400_BAD_REQUEST)
        
        results = []
        errors = []
        success_count = 0
        skipped_count = 0
        
        from nanoid import generate
        from .models import Dataset
        
        for i, dataset_item in enumerate(datasets_data):
            try:
                # 验证必填字段
                question = dataset_item.get('question', '').strip() if isinstance(dataset_item.get('question'), str) else ''
                answer = dataset_item.get('answer', '').strip() if isinstance(dataset_item.get('answer'), str) else ''
                
                if not question or not answer:
                    errors.append(f'第 {i + 1} 条记录缺少必填字段(question/answer)，已跳过')
                    skipped_count += 1
                    continue
                
                # 处理可选字段
                chunk_name = dataset_item.get('chunkName', 'Imported Data')
                chunk_content = dataset_item.get('chunkContent', 'Imported from external source')
                model = dataset_item.get('model', 'imported')
                question_label = dataset_item.get('questionLabel', '')
                cot = dataset_item.get('cot', '') if isinstance(dataset_item.get('cot'), str) else ''
                confirmed = bool(dataset_item.get('confirmed', False))
                score = int(dataset_item.get('score', 0)) if isinstance(dataset_item.get('score'), (int, float)) else 0
                
                # 处理tags字段
                tags = dataset_item.get('tags', [])
                if isinstance(tags, list):
                    tags_str = json.dumps(tags, ensure_ascii=False)
                elif isinstance(tags, str):
                    tags_str = tags
                elif isinstance(tags, dict):
                    tags_str = json.dumps(tags, ensure_ascii=False)
                else:
                    tags_str = '[]'
                
                # 处理other字段
                other = dataset_item.get('other', {})
                if isinstance(other, dict):
                    other_str = json.dumps(other, ensure_ascii=False)
                elif isinstance(other, str):
                    other_str = other
                else:
                    other_str = '{}'
                
                note = dataset_item.get('note', '') if isinstance(dataset_item.get('note'), str) else ''
                
                # 创建数据集
                dataset = Dataset.objects.create(
                    id=generate(size=12),
                    project=project,
                    question_id=generate(size=12),  # 生成问题ID
                    question=question,
                    answer=answer,
                    chunk_name=chunk_name,
                    chunk_content=chunk_content,
                    model=model,
                    question_label=question_label,
                    cot=cot,
                    confirmed=confirmed,
                    score=score,
                    tags=tags_str,
                    note=note,
                    other=other_str
                )
                
                results.append({
                    'id': dataset.id,
                    'question': dataset.question
                })
                success_count += 1
            except Exception as e:
                errors.append(f'第 {i + 1} 条记录: {str(e)}')
        
        return success(data={
            'success': success_count,
            'total': len(datasets_data),
            'failed': len(errors),
            'skipped': skipped_count,
            'errors': errors,
            'sourceInfo': source_info
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

