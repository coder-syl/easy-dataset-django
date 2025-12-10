"""
文本块名称批量更新视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from projects.models import Project
from .models import Chunk
from common.response.result import success, error


@swagger_auto_schema(
    method='put',
    operation_summary='批量更新文本块名称',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'items': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'chunkId': openapi.Schema(type=openapi.TYPE_STRING),
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        }
    ),
    responses={200: openapi.Response('更新结果')}
)
@api_view(['PUT'])
def chunk_update_name(request, project_id):
    """
    批量更新文本块名称
    请求体: { items: [ {chunkId, name}, ... ] }
    """
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)

    items = request.data.get('items', [])
    if not isinstance(items, list) or len(items) == 0:
        return error(message='items 不能为空', response_status=status.HTTP_400_BAD_REQUEST)

    updated = 0
    errors = []
    for item in items:
        cid = item.get('chunkId')
        new_name = item.get('name')
        if not cid or new_name is None:
            errors.append({'chunkId': cid, 'error': '缺少chunkId或name'})
            continue
        try:
            chunk = Chunk.objects.get(id=cid, project=project)
            chunk.name = new_name
            chunk.save()
            updated += 1
        except Chunk.DoesNotExist:
            errors.append({'chunkId': cid, 'error': '文本块不存在'})
        except Exception as e:
            errors.append({'chunkId': cid, 'error': str(e)})

    return success(data={
        'updated': updated,
        'errors': errors
    })

