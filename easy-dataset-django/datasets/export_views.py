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
    export_datasets_to_json,
    export_datasets_to_csv,
    export_datasets_to_jsonl,
    get_tag_statistics
)
from common.response.result import success, error


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
            'balanceConfig': openapi.Schema(type=openapi.TYPE_OBJECT),
            'confirmed': openapi.Schema(type=openapi.TYPE_BOOLEAN),
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
            return success(data=stats)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        # 导出数据集
        try:
            # 获取查询参数
            format_type = request.GET.get('format', 'json')  # json, csv, jsonl
            export_format = request.GET.get('exportFormat', 'standard')  # standard, huggingface, llamafactory
            confirmed_param = request.GET.get('confirmed')
            confirmed = None if confirmed_param is None else (confirmed_param.lower() == 'true')
            
            # 获取请求体
            body = request.data if hasattr(request, 'data') else {}
            selected_ids = body.get('selectedIds')
            balance_config = body.get('balanceConfig')
            
            # 获取数据集
            datasets = get_datasets_for_export(
                project_id,
                confirmed=confirmed,
                selected_ids=selected_ids,
                balance_config=balance_config
            )
            
            # 根据格式导出
            if format_type == 'csv':
                content = export_datasets_to_csv(datasets)
                response = HttpResponse(content, content_type='text/csv; charset=utf-8')
                response['Content-Disposition'] = f'attachment; filename="datasets_{project_id}.csv"'
                return response
            elif format_type == 'jsonl':
                content = export_datasets_to_jsonl(datasets, export_format)
                response = HttpResponse(content, content_type='text/plain; charset=utf-8')
                response['Content-Disposition'] = f'attachment; filename="datasets_{project_id}.jsonl"'
                return response
            else:
                # JSON格式
                content = export_datasets_to_json(datasets, export_format)
                response = HttpResponse(content, content_type='application/json; charset=utf-8')
                response['Content-Disposition'] = f'attachment; filename="datasets_{project_id}.json"'
                return response
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

