"""
项目导出相关视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from pathlib import Path
import json

from .models import Project
from datasets.models import Dataset
from common.response.result import success, error
import requests
import tempfile
import os
from django.http import FileResponse, Http404


@swagger_auto_schema(
    method='post',
    operation_summary='上传数据集到HuggingFace',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'token': openapi.Schema(type=openapi.TYPE_STRING),
            'datasetName': openapi.Schema(type=openapi.TYPE_STRING),
            'isPrivate': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'formatType': openapi.Schema(type=openapi.TYPE_STRING),
            'systemPrompt': openapi.Schema(type=openapi.TYPE_STRING),
            'confirmedOnly': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'includeCOT': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'fileFormat': openapi.Schema(type=openapi.TYPE_STRING),
            'customFields': openapi.Schema(type=openapi.TYPE_OBJECT),
            'reasoningLanguage': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('上传成功')}
)
@api_view(['POST'])
def huggingface_upload(request, project_id):
    """上传数据集到HuggingFace"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        token = request.data.get('token')
        dataset_name = request.data.get('datasetName')
        is_private = request.data.get('isPrivate', False)
        format_type = request.data.get('formatType', 'alpaca')
        system_prompt = request.data.get('systemPrompt', '')
        confirmed_only = request.data.get('confirmedOnly', False)
        include_cot = request.data.get('includeCOT', False)
        file_format = request.data.get('fileFormat', 'json')
        custom_fields = request.data.get('customFields')
        reasoning_language = request.data.get('reasoningLanguage', 'English')
        
        if not token or not dataset_name:
            return error(message='Token和数据集名称不能为空', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 获取数据集
        queryset = Dataset.objects.filter(project=project)
        if confirmed_only:
            queryset = queryset.filter(confirmed=True)
        datasets = list(queryset)
        if not datasets:
            return error(message='没有可用的数据集', response_status=status.HTTP_400_BAD_REQUEST)

        # 构建导出数据
        def _build_alpaca():
            return [{
                'instruction': d.question,
                'input': '',
                'output': f'<think>{d.cot}</think>\n{d.answer}' if (include_cot and d.cot) else d.answer,
                'system': system_prompt or ''
            } for d in datasets]

        if file_format == 'jsonl':
            content = '\n'.join([json.dumps(item, ensure_ascii=False) for item in _build_alpaca()])
            mime = 'text/plain'
            filename = f'{dataset_name}.jsonl'
        else:
            content = json.dumps(_build_alpaca(), ensure_ascii=False, indent=2)
            mime = 'application/json'
            filename = f'{dataset_name}.json'

        # 写入临时文件
        tmpdir = tempfile.mkdtemp()
        file_path = Path(tmpdir) / filename
        file_path.write_text(content, encoding='utf-8')

        # 尝试通过 HuggingFace Hub HTTP API 上传
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        create_resp = requests.post(
            'https://huggingface.co/api/repos/create',
            json={'name': dataset_name, 'type': 'dataset', 'private': is_private},
            headers=headers,
            timeout=20
        )
        # 如果已存在会返回409，视为可继续
        if create_resp.status_code not in (200, 201, 409):
            return error(message=f'创建数据集失败: {create_resp.text}', response_status=status.HTTP_502_BAD_GATEWAY)

        upload_url = f"https://huggingface.co/api/datasets/{dataset_name}/upload/file"
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, mime)}
            upload_resp = requests.post(upload_url, headers=headers, files=files, timeout=30)
        if upload_resp.status_code not in (200, 201):
            return error(message=f'上传文件失败: {upload_resp.text}', response_status=status.HTTP_502_BAD_GATEWAY)

        return success(data={
            'message': '上传成功',
            'datasetName': dataset_name,
            'file': filename,
            'count': len(datasets),
            'huggingface': upload_resp.json() if upload_resp.headers.get('content-type', '').startswith('application/json') else upload_resp.text
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def llama_factory_download(request, project_id):
    """下载已生成的 LLaMA Factory 文件，参数 file 为文件名（相对于项目 local-db 目录）"""
    try:
        # 安全校验项目是否存在
        _ = get_object_or_404(Project, id=project_id)
        file_name = request.query_params.get('file') or request.GET.get('file')
        if not file_name:
            return error(message='file 参数缺失', response_status=status.HTTP_400_BAD_REQUEST)
        project_path = Path('local-db') / project_id
        # Normalize and resolve requested file path. Support these cases:
        # - file is a relative path under the project subdir (e.g. "single/dataset_info.json")
        # - file is a path that already contains "local-db/<project_id>/..." (frontend may return full path)
        # - file is an absolute path on disk
        try:
            req = Path(file_name)
        except Exception:
            return error(message='非法的文件路径', response_status=status.HTTP_400_BAD_REQUEST)

        if req.is_absolute():
            target_path = req.resolve()
        else:
            s = str(file_name).replace('\\', '/').lstrip('/')
            prefix = f'local-db/{project_id}/'
            if s.startswith(prefix):
                rel = s[len(prefix):]
                target_path = (project_path / rel).resolve()
            else:
                # try to find project_id in the string and strip up to it
                marker = f'/{project_id}/'
                idx = s.find(marker)
                if idx != -1:
                    rel = s[idx + len(marker):]
                    target_path = (project_path / rel).resolve()
                else:
                    # treat as relative to project_path
                    target_path = (project_path / s).resolve()

        # 防止目录穿越：确保目标路径位于项目 local-db/<project_id> 目录或其子目录中
        try:
            project_resolved = project_path.resolve()
            if not str(target_path).startswith(str(project_resolved)):
                return error(message='非法的文件路径', response_status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error(message='内部路径解析错误', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not target_path.exists() or not target_path.is_file():
            return error(message='文件不存在', response_status=status.HTTP_404_NOT_FOUND)

        # 返回文件流作为附件下载
        return FileResponse(open(target_path, 'rb'), as_attachment=True, filename=target_path.name)
    except Http404:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='检查LLaMA Factory配置',
    responses={200: openapi.Response('配置信息')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='生成LLaMA Factory配置',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'formatType': openapi.Schema(type=openapi.TYPE_STRING),
            'systemPrompt': openapi.Schema(type=openapi.TYPE_STRING),
            'confirmedOnly': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'includeCOT': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'reasoningLanguage': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('生成成功')}
)
@api_view(['GET', 'POST'])
def llama_factory_config(request, project_id):
    """检查或生成LLaMA Factory配置"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            # 检查配置文件是否存在
            project_path = Path('local-db') / project_id
            dataset_type = request.GET.get('datasetType') or request.query_params.get('datasetType') if hasattr(request, 'query_params') else request.GET.get('datasetType')
            if not dataset_type:
                dataset_type = 'single'
            # store configs per dataset type under subfolder
            project_subpath = project_path / dataset_type
            config_path = project_subpath / 'dataset_info.json'
            
            exists = config_path.exists()
            
            return success(data={
                'exists': exists,
                'configPath': str(config_path) if exists else None
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # POST: 生成配置和数据文件
    try:
        format_type = request.data.get('formatType', 'alpaca')
        system_prompt = request.data.get('systemPrompt', '')
        confirmed_only = request.data.get('confirmedOnly', False)
        include_cot = request.data.get('includeCOT', False)
        reasoning_language = request.data.get('reasoningLanguage', 'English')
        dataset_type = request.data.get('datasetType', 'single')
        
        # 获取数据集
        queryset = Dataset.objects.filter(project=project)
        if confirmed_only:
            queryset = queryset.filter(confirmed=True)
        
        datasets = list(queryset)
        
        # 创建项目目录
        project_path = Path('local-db') / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        # create/type-specific subfolder
        project_subpath = project_path / dataset_type
        project_subpath.mkdir(parents=True, exist_ok=True)
        
        config_path = project_subpath / 'dataset_info.json'
        alpaca_path = project_subpath / 'alpaca.json'
        sharegpt_path = project_subpath / 'sharegpt.json'
        multilingual_thinking_path = project_subpath / 'multilingual-thinking.json'
        
        # 创建配置
        config = {
            f'[Easy-Fine-Tunning] [{project_id}] Alpaca': {
                'file_name': 'alpaca.json',
                'columns': {
                    'prompt': 'instruction',
                    'query': 'input',
                    'response': 'output',
                    'system': 'system'
                }
            },
            f'[Easy-Fine-Tunning] [{project_id}] ShareGPT': {
                'file_name': 'sharegpt.json',
                'formatting': 'sharegpt',
                'columns': {
                    'messages': 'messages'
                },
                'tags': {
                    'role_tag': 'role',
                    'content_tag': 'content',
                    'user_tag': 'user',
                    'assistant_tag': 'assistant',
                    'system_tag': 'system'
                }
            },
            f'[Easy-Fine-Tunning] [{project_id}] multilingual-thinking': {
                'file_name': 'multilingual-thinking.json',
                'formatting': 'multilingual-thinking',
                'columns': {
                    'messages': 'messages'
                },
                'tags': {
                    'role_tag': 'role',
                    'content_tag': 'content',
                    'user_tag': 'user',
                    'assistant_tag': 'assistant',
                    'system_tag': 'system'
                }
            }
        }
        
        # 生成数据文件
        alpaca_data = [{
            'instruction': d.question,
            'input': '',
            'output': f'<think>{d.cot}</think>\n{d.answer}' if (include_cot and d.cot) else d.answer,
            'system': system_prompt or ''
        } for d in datasets]
        
        sharegpt_data = []
        for d in datasets:
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': d.question})
            messages.append({
                'role': 'assistant',
                'content': f'<think>{d.cot}</think>\n{d.answer}' if (include_cot and d.cot) else d.answer
            })
            sharegpt_data.append({'messages': messages})
        
        multilingual_thinking_data = [{
            'reasoning_language': reasoning_language,
            'developer': system_prompt or '',
            'user': d.question,
            'analysis': d.cot if (include_cot and d.cot) else None,
            'final': d.answer,
            'messages': [
                {'content': system_prompt or '', 'role': 'system', 'thinking': None},
                {'content': d.question, 'role': 'user', 'thinking': None},
                {'content': d.answer, 'role': 'assistant', 'thinking': d.cot if (include_cot and d.cot) else None}
            ]
        } for d in datasets]
        
        # 写入文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        with open(alpaca_path, 'w', encoding='utf-8') as f:
            json.dump(alpaca_data, f, ensure_ascii=False, indent=2)
        
        with open(sharegpt_path, 'w', encoding='utf-8') as f:
            json.dump(sharegpt_data, f, ensure_ascii=False, indent=2)
        
        multilingual_thinking_lines = '\n'.join([json.dumps(item, ensure_ascii=False) for item in multilingual_thinking_data])
        with open(multilingual_thinking_path, 'w', encoding='utf-8') as f:
            f.write(multilingual_thinking_lines)
        
        return success(data={
            'success': True,
            'configPath': str(config_path),
            'files': [
                {'path': str(config_path), 'format': 'config'},
                {'path': str(alpaca_path), 'format': 'alpaca'},
                {'path': str(sharegpt_path), 'format': 'sharegpt'},
                {'path': str(multilingual_thinking_path), 'format': 'multilingual-thinking'}
            ]
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 兼容旧路由：直接调用 llama_factory_config 的逻辑
@api_view(['POST'])
def llama_factory_generate(request, project_id):
    """
    兼容旧路由：委托给 llama_factory_config
    这里需要传入原生 HttpRequest，否则 DRF 的 Request 会触发断言错误
    """
    django_request = getattr(request, '_request', request)
    return llama_factory_config(django_request, project_id)

