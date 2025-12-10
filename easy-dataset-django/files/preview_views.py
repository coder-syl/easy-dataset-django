"""
文件预览视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
from pathlib import Path

from projects.models import Project
from .models import UploadFile
from common.response.result import success, error


@swagger_auto_schema(
    method='get',
    operation_summary='预览文件',
    responses={200: openapi.Response('文件内容')}
)
@api_view(['GET'])
def file_preview(request, project_id, file_id):
    """预览文件内容"""
    try:
        project = get_object_or_404(Project, id=project_id)
        upload_file = get_object_or_404(UploadFile, id=file_id, project=project)
    except Exception as e:
        return error(message='文件不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    try:
        file_path = Path(upload_file.path) / upload_file.file_name
        
        # 检查是否存在对应的Markdown文件
        md_file_name = upload_file.file_name
        file_ext = Path(upload_file.file_name).suffix.lower()
        
        if file_ext in ['.pdf', '.docx', '.epub']:
            md_file_name = md_file_name.replace(file_ext, '.md')
        
        md_file_path = Path(upload_file.path) / md_file_name
        
        # 优先返回Markdown文件内容
        if md_file_path.exists():
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 与 Node.js 保持一致：直接返回 JSON，不使用 success() 包装
            from rest_framework.response import Response
            return Response({
                'fileId': file_id,
                'fileName': upload_file.file_name,
                'content': content
            }, status=status.HTTP_200_OK)
        elif file_path.exists():
            # 如果Markdown文件不存在，读取原始文件
            if file_ext in ['.md', '.txt', '.markdown']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 与 Node.js 保持一致：返回 JSON 格式
                return success(data={
                    'fileId': file_id,
                    'fileName': upload_file.file_name,
                    'content': content
                })
            else:
                return error(message='不支持预览此文件类型', response_status=status.HTTP_400_BAD_REQUEST)
        else:
            return error(message='文件不存在', response_status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return error(message=f'预览文件失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

