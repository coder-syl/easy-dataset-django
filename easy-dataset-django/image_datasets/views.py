"""
图像数据集管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from pathlib import Path
import base64

from projects.models import Project
from images.models import Image
from .models import ImageDataset
from .serializers import ImageDatasetSerializer, ImageDatasetCreateSerializer
from common.response.result import success, error


def get_image_base64(project_id, image_name):
    """获取图片的base64编码"""
    try:
        project_path = Path('local-db') / project_id / 'images'
        image_path = project_path / image_name
        
        if not image_path.exists():
            return None
        
        with open(image_path, 'rb') as f:
            image_buffer = f.read()
        
        ext = image_path.suffix.lower()
        mime_type = 'image/png' if ext == '.png' else 'image/gif' if ext == '.gif' else 'image/jpeg'
        
        base64_data = base64.b64encode(image_buffer).decode('utf-8')
        return f'data:{mime_type};base64,{base64_data}'
    except Exception as e:
        return None


@swagger_auto_schema(
    method='get',
    operation_summary='获取图像数据集列表',
    responses={200: openapi.Response('数据集列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='生成图像数据集',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'imageName': openapi.Schema(type=openapi.TYPE_STRING),
            'question': openapi.Schema(type=openapi.TYPE_STRING),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('生成成功')}
)
@api_view(['GET', 'POST'])
def image_dataset_list_create(request, project_id):
    """获取图像数据集列表或生成图像数据集"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('pageSize', 20))
            search = request.GET.get('search', '')
            confirmed = request.GET.get('confirmed')
            min_score = request.GET.get('minScore')
            max_score = request.GET.get('maxScore')
            
            queryset = ImageDataset.objects.filter(project=project)
            
            if search:
                queryset = queryset.filter(
                    Q(question__icontains=search) | Q(answer__icontains=search)
                )
            
            if confirmed is not None:
                queryset = queryset.filter(confirmed=confirmed == 'true')
            
            if min_score:
                queryset = queryset.filter(score__gte=float(min_score))
            if max_score:
                queryset = queryset.filter(score__lte=float(max_score))
            
            paginator = Paginator(queryset.order_by('-create_at'), page_size)
            page_obj = paginator.get_page(page)
            
            # 为每个数据集添加图片base64
            datasets_with_images = []
            for dataset in page_obj.object_list:
                dataset_data = ImageDatasetSerializer(dataset).data
                base64_image = get_image_base64(project_id, dataset.image_name)
                dataset_data['base64'] = base64_image
                datasets_with_images.append(dataset_data)
            
            return success(data={
                'data': datasets_with_images,
                'total': paginator.count,
                'page': page,
                'pageSize': page_size
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            # 生成图像数据集（暂时返回占位响应，后续需要集成LLM调用逻辑）
            image_name = request.data.get('imageName')
            question = request.data.get('question')
            model = request.data.get('model')
            language = request.data.get('language', 'zh')
            preview_only = request.data.get('previewOnly', False)
            
            if not image_name or not question:
                return error(message='缺少必要参数', response_status=status.HTTP_400_BAD_REQUEST)
            
            if not model:
                return error(message='请选择一个视觉模型', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 获取图片信息
            image = Image.objects.filter(project=project, image_name=image_name).first()
            if not image:
                return error(message='图片不存在', response_status=status.HTTP_404_NOT_FOUND)
            
            # 集成图像数据集生成逻辑
            from images.services import generate_dataset_for_image
            
            try:
                result = generate_dataset_for_image(
                    project_id,
                    image.id,
                    question,
                    {
                        'model': model,
                        'language': language,
                        'previewOnly': preview_only
                    }
                )
                
                return success(data=result)
            except Exception as e:
                return error(message=f'生成图像数据集失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取图像数据集详情',
    responses={200: openapi.Response('数据集详情')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新图像数据集',
    request_body=ImageDatasetSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除图像数据集',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'PUT', 'DELETE'])
def image_dataset_detail_update_delete(request, project_id, dataset_id):
    """获取、更新或删除图像数据集"""
    try:
        project = get_object_or_404(Project, id=project_id)
        dataset = get_object_or_404(ImageDataset, id=dataset_id, project=project)
    except Exception as e:
        return error(message='数据集不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            serializer = ImageDatasetSerializer(dataset)
            dataset_data = serializer.data
            
            # 添加base64
            base64_image = get_image_base64(project_id, dataset.image_name)
            dataset_data['base64'] = base64_image
            
            return success(data=dataset_data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            serializer = ImageDatasetSerializer(dataset, data=request.data, partial=True)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            dataset.delete()
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
