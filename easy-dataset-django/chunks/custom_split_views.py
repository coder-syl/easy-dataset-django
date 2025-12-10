"""
自定义分割视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from pathlib import Path
from nanoid import generate

from projects.models import Project
from files.models import UploadFile
from .models import Chunk
from common.response.result import success, error


@swagger_auto_schema(
    method='post',
    operation_summary='自定义分割',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'fileId': openapi.Schema(type=openapi.TYPE_STRING),
            'fileName': openapi.Schema(type=openapi.TYPE_STRING),
            'content': openapi.Schema(type=openapi.TYPE_STRING),
            'splitPoints': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'position': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            )
        }
    ),
    responses={200: openapi.Response('分割成功')}
)
@api_view(['POST'])
def custom_split(request, project_id):
    """自定义分割"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        file_id = request.data.get('fileId')
        file_name = request.data.get('fileName')
        content = request.data.get('content')
        split_points = request.data.get('splitPoints', [])
        
        if not all([file_id, file_name, content, split_points]):
            return error(message='Missing required parameters', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 先删除该文件已有的文本块
        Chunk.objects.filter(project=project, file_id=file_id).delete()
        
        # 根据分块点生成文本块
        sorted_points = sorted(split_points, key=lambda x: x.get('position', 0))
        
        chunks = []
        start_pos = 0
        
        for i, point in enumerate(sorted_points):
            end_pos = point.get('position', 0)
            chunk_content = content[start_pos:end_pos]
            
            if chunk_content.strip():
                chunk = Chunk.objects.create(
                    id=generate(size=12),
                    project=project,
                    file_id=file_id,
                    file_name=file_name,
                    name=f"{Path(file_name).stem}-part-{i + 1}",
                    content=chunk_content,
                    summary=f"{file_name} 自定义分块 {i + 1}/{len(sorted_points) + 1}",
                    size=len(chunk_content)
                )
                chunks.append(chunk)
            
            start_pos = end_pos
        
        # 添加最后一个分块
        last_chunk_content = content[start_pos:]
        if last_chunk_content.strip():
            chunk = Chunk.objects.create(
                id=generate(size=12),
                project=project,
                file_id=file_id,
                file_name=file_name,
                name=f"{Path(file_name).stem}-part-{len(sorted_points) + 1}",
                content=last_chunk_content,
                summary=f"{file_name} 自定义分块 {len(sorted_points) + 1}/{len(sorted_points) + 1}",
                size=len(last_chunk_content)
            )
            chunks.append(chunk)
        
        return success(data={
            'success': True,
            'message': 'Custom chunks saved successfully',
            'totalChunks': len(chunks)
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

