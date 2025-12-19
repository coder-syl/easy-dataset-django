"""
图像管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from pathlib import Path
import base64

from projects.models import Project
from questions.models import Question
from image_datasets.models import ImageDataset
from .models import Image
from .serializers import ImageSerializer
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
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        base64_data = base64.b64encode(image_buffer).decode('utf-8')
        return f'data:{mime_type};base64,{base64_data}'
    except Exception as e:
        return None


@swagger_auto_schema(
    method='get',
    operation_summary='获取图片列表',
    responses={200: openapi.Response('图片列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='导入图片',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={'directories': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))}
    ),
    responses={200: openapi.Response('导入成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除图片',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'POST', 'DELETE'])
def image_list_import_delete(request, project_id):
    """图片列表、导入、删除"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('pageSize', 20))
            image_name = request.GET.get('imageName', '')
            has_questions = request.GET.get('hasQuestions')
            has_datasets = request.GET.get('hasDatasets')
            simple = request.GET.get('simple')
            
            queryset = Image.objects.filter(project=project)
            
            if image_name:
                queryset = queryset.filter(image_name__icontains=image_name)
            
            # 如果只需要简单列表
            if simple:
                serializer = ImageSerializer(queryset.order_by('-create_at'), many=True)
                return success(data={'data': serializer.data})
            
            # 优化查询：使用 Count 聚合
            # 注意：question_count 需要关联到 questions 表，但 image_id 在 Question 中是 CharField，不是 ForeignKey
            # 所以这里可能需要手动聚合或改用更高效的方式
            
            images_with_stats = []
            # 获取所有问题的图片统计
            question_counts = Question.objects.filter(
                project=project, 
                image_id__isnull=False
            ).values('image_id').annotate(count=Count('id'))
            question_count_map = {item['image_id']: item['count'] for item in question_counts}
            
            # 获取所有数据集的图片统计
            dataset_counts = ImageDataset.objects.filter(
                project=project
            ).values('image_id').annotate(count=Count('id'))
            dataset_count_map = {item['image_id']: item['count'] for item in dataset_counts}
            
            for image in queryset.order_by('-create_at'):
                q_count = question_count_map.get(str(image.id), 0)
                d_count = dataset_count_map.get(str(image.id), 0)
                
                # 应用筛选
                if has_questions == 'true' and q_count == 0:
                    continue
                if has_questions == 'false' and q_count > 0:
                    continue
                if has_datasets == 'true' and d_count == 0:
                    continue
                if has_datasets == 'false' and d_count > 0:
                    continue
                
                image_data = ImageSerializer(image).data
                image_data['questionCount'] = q_count
                image_data['datasetCount'] = d_count
                
                # 添加base64
                base64_image = get_image_base64(project_id, image.image_name)
                image_data['base64'] = base64_image
                
                images_with_stats.append(image_data)
            
            # 分页
            total = len(images_with_stats)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_images = images_with_stats[start_index:end_index]
            
            return success(data={
                'data': paginated_images,
                'total': total,
                'page': page,
                'pageSize': page_size
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            # 导入图片（暂时返回占位响应，后续需要集成文件处理逻辑）
            directories = request.data.get('directories', [])
            
            # 集成图片导入逻辑
            from .services import import_images_from_directories
            
            try:
                result = import_images_from_directories(project_id, directories)
                return success(data=result)
            except Exception as e:
                return error(message=f'导入图片失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            image_id = request.GET.get('imageId')
            if not image_id:
                return error(message='图片ID不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            image = get_object_or_404(Image, id=image_id, project=project)
            
            # 删除关联的数据集
            ImageDataset.objects.filter(image_id=image_id).delete()
            
            # 删除关联的问题
            Question.objects.filter(image_id=image_id).delete()
            
            # 删除文件
            project_path = Path('local-db') / project_id / 'images'
            file_path = project_path / image.image_name
            if file_path.exists():
                file_path.unlink()
            
            # 删除数据库记录
            image.delete()
            
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取图片详情',
    responses={200: openapi.Response('图片详情')}
)
@api_view(['GET'])
def image_detail(request, project_id, image_id):
    """获取图片详情（包含问题列表和已标注数据）"""
    try:
        from .services import getImageDetailWithQuestions
        result = getImageDetailWithQuestions(project_id, image_id)
        return success(data=result)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
