"""
工具类API视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from pathlib import Path
import json
import os
import requests

from projects.models import Project
from datasets.models import Dataset
from common.response.result import success, error


@swagger_auto_schema(
    method='post',
    operation_summary='从模型提供商获取模型列表',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'endpoint': openapi.Schema(type=openapi.TYPE_STRING),
            'providerId': openapi.Schema(type=openapi.TYPE_STRING),
            'apiKey': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('模型列表')}
)
@api_view(['POST'])
def fetch_models(request):
    """从模型提供商获取模型列表"""
    try:
        endpoint = request.data.get('endpoint')
        provider_id = request.data.get('providerId')
        api_key = request.data.get('apiKey')
        
        if not endpoint:
            return error(message='缺少 endpoint 参数', response_status=status.HTTP_400_BAD_REQUEST)
        
        url = endpoint.rstrip('/')
        
        # 处理 Ollama endpoint
        if provider_id == 'ollama':
            url = url.replace(r'/v\d+$', '')
            if '/api' not in url:
                url += '/api'
            url += '/tags'
        else:
            url += '/models'
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 根据不同提供商格式化返回数据
        formatted_models = []
        data = response.json()
        
        if provider_id == 'ollama':
            if 'models' in data and isinstance(data['models'], list):
                formatted_models = [{
                    'modelId': item['name'],
                    'modelName': item['name'],
                    'providerId': provider_id
                } for item in data['models']]
        else:
            if 'data' in data and isinstance(data['data'], list):
                formatted_models = [{
                    'modelId': item['id'],
                    'modelName': item['id'],
                    'providerId': provider_id
                } for item in data['data']]
        
        return success(data=formatted_models)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='检查更新',
    responses={200: openapi.Response('更新信息')}
)
@api_view(['GET'])
def check_update(request):
    """检查应用更新"""
    try:
        # 获取当前版本
        package_json_path = Path('package.json')
        if package_json_path.exists():
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_json = json.load(f)
                current_version = package_json.get('version', '1.0.0')
        else:
            current_version = '1.0.0'
        
        # 从 GitHub 获取最新版本
        try:
            owner = 'ConardLi'
            repo = 'easy-dataset'
            response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}/releases/latest',
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            latest_version = data.get('tag_name', '').replace('v', '')
            
            # 简单的版本比较
            def compare_versions(a, b):
                parts_a = [int(x) for x in a.split('.')]
                parts_b = [int(x) for x in b.split('.')]
                for i in range(max(len(parts_a), len(parts_b))):
                    num_a = parts_a[i] if i < len(parts_a) else 0
                    num_b = parts_b[i] if i < len(parts_b) else 0
                    if num_a > num_b:
                        return 1
                    if num_a < num_b:
                        return -1
                return 0
            
            has_update = compare_versions(latest_version, current_version) > 0
            
            return success(data={
                'hasUpdate': has_update,
                'currentVersion': current_version,
                'latestVersion': latest_version,
                'releaseUrl': f'https://github.com/{owner}/{repo}/releases/tag/v{latest_version}' if has_update else None
            })
        except Exception as e:
            return success(data={
                'hasUpdate': False,
                'currentVersion': current_version,
                'latestVersion': None,
                'error': '获取最新版本失败'
            })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='执行更新',
    responses={200: openapi.Response('更新结果')}
)
@api_view(['POST'])
def execute_update(request):
    """执行应用更新"""
    try:
        # 检查是否在客户端环境中运行
        desktop_dir = Path('desktop')
        updater_path = desktop_dir / 'scripts' / 'updater.js'
        
        if not updater_path.exists():
            return error(
                message='更新功能仅在客户端环境中可用',
                response_status=status.HTTP_400_BAD_REQUEST
            )
        
        import subprocess
        proc = subprocess.run(
            ['node', str(updater_path)],
            cwd=str(desktop_dir),
            capture_output=True,
            text=True,
            timeout=300
        )
        if proc.returncode != 0:
            return error(message=f'更新失败: {proc.stderr}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return success(data={
            'success': True,
            'stdout': proc.stdout
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

