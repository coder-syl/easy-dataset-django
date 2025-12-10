"""
图像高级功能视图占位
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from pathlib import Path
import zipfile
import tempfile
import fitz  # PyMuPDF

from projects.models import Project
from .models import Image
from .services import import_images_from_directories, generate_questions_for_image, generate_dataset_for_image
from common.response.result import success, error
from nanoid import generate


def _ensure_project(project_id):
    return get_object_or_404(Project, id=project_id)


def _save_image_file(project_id: str, file_name: str, data: bytes) -> Image:
    """保存图片文件并创建记录"""
    project = Project.objects.get(id=project_id)
    images_dir = Path('local-db') / project_id / 'images'
    images_dir.mkdir(parents=True, exist_ok=True)
    dest = images_dir / file_name
    with open(dest, 'wb') as f:
        f.write(data)
    img = Image.objects.create(
        id=generate(size=12),
        project=project,
        image_name=file_name,
        image_ext=dest.suffix,
        path=str(images_dir),
        size=dest.stat().st_size
    )
    return img


@swagger_auto_schema(
    method='post',
    operation_summary='上传单个图像',
    manual_parameters=[
        openapi.Parameter('x-file-name', openapi.IN_HEADER, type=openapi.TYPE_STRING, description='文件名')
    ]
)
@api_view(['POST'])
def upload_image(request, project_id):
    """单图上传"""
    _ensure_project(project_id)
    file_name = request.headers.get('x-file-name') or request.headers.get('X-File-Name')
    if not file_name:
        return error(message='缺少x-file-name', response_status=status.HTTP_400_BAD_REQUEST)
    if not request.body:
        return error(message='文件内容为空', response_status=status.HTTP_400_BAD_REQUEST)
    try:
        img = _save_image_file(project_id, file_name, request.body)
        return success(data={'id': str(img.id), 'fileName': img.image_name})
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(method='post', operation_summary='ZIP导入图像')
@api_view(['POST'])
def zip_import(request, project_id):
    """支持上传zip文件或提供directories列表"""
    _ensure_project(project_id)
    # 1) 若有zip文件
    if request.FILES:
        up_file = next(iter(request.FILES.values()))
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpzip = Path(tmpdir) / up_file.name
            for chunk in up_file.chunks():
                with open(tmpzip, 'ab') as f:
                    f.write(chunk)
            extract_dir = Path(tmpdir) / 'extract'
            extract_dir.mkdir()
            with zipfile.ZipFile(tmpzip, 'r') as zf:
                zf.extractall(extract_dir)
            result = import_images_from_directories(project_id, [str(extract_dir)])
            return success(data=result)
    # 2) directories列表
    directories = request.data.get('directories', [])
    result = import_images_from_directories(project_id, directories)
    return success(data=result)


@swagger_auto_schema(method='post', operation_summary='PDF转图像', request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'fileName': openapi.Schema(type=openapi.TYPE_STRING),
        'pdfBase64': openapi.Schema(type=openapi.TYPE_STRING)
    }
))
@api_view(['POST'])
def pdf_convert(request, project_id):
    """将PDF页面转为图片并入库"""
    _ensure_project(project_id)
    file_name = request.data.get('fileName') or 'document.pdf'
    pdf_base64 = request.data.get('pdfBase64')
    if not pdf_base64:
        return error(message='缺少pdfBase64', response_status=status.HTTP_400_BAD_REQUEST)
    try:
        import base64
        pdf_bytes = base64.b64decode(pdf_base64)
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / file_name
            pdf_path.write_bytes(pdf_bytes)
            doc = fitz.open(pdf_path)
            saved = []
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                img_name = f"{Path(file_name).stem}_p{i+1}.png"
                img_bytes = pix.tobytes("png")
                img = _save_image_file(project_id, img_name, img_bytes)
                saved.append({'id': str(img.id), 'fileName': img.image_name})
            doc.close()
        return success(data={'imported': len(saved), 'images': saved})
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(method='get', operation_summary='获取下一个未回答图像')
@api_view(['GET'])
def next_unanswered(request, project_id):
    """获取未有问题的数据集中第一张"""
    _ensure_project(project_id)
    img = Image.objects.filter(project_id=project_id).first()
    if not img:
        return success(data={'imageId': None})
    return success(data={'imageId': str(img.id), 'imageName': img.image_name})


@swagger_auto_schema(method='post', operation_summary='创建图像标注')
@api_view(['POST'])
def annotations(request, project_id):
    """简单将标注内容写入note"""
    _ensure_project(project_id)
    image_id = request.data.get('imageId')
    note = request.data.get('note', '')
    if not image_id:
        return error(message='imageId不能为空', response_status=status.HTTP_400_BAD_REQUEST)
    try:
        image = Image.objects.get(id=image_id, project_id=project_id)
        image.note = note
        image.save()
        return success(data={'id': str(image.id), 'note': image.note})
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(method='post', operation_summary='生成图像问题')
@api_view(['POST'])
def generate_questions(request, project_id):
    _ensure_project(project_id)
    image_id = request.data.get('imageId')
    model = request.data.get('model')
    language = request.data.get('language', 'zh')
    count = request.data.get('count', 3)
    if not image_id or not model:
        return error(message='imageId和model必填', response_status=status.HTTP_400_BAD_REQUEST)
    try:
        result = generate_questions_for_image(project_id, image_id, {
            'model': model,
            'language': language,
            'count': count
        })
        return success(data=result)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(method='post', operation_summary='生成图像数据集')
@api_view(['POST'])
def generate_datasets(request, project_id):
    _ensure_project(project_id)
    image_id = request.data.get('imageId')
    question = request.data.get('question')
    model = request.data.get('model')
    language = request.data.get('language', 'zh')
    preview_only = request.data.get('previewOnly', False)
    if not all([image_id, question, model]):
        return error(message='imageId/question/model 不能为空', response_status=status.HTTP_400_BAD_REQUEST)
    try:
        result = generate_dataset_for_image(project_id, image_id, question, {
            'model': model,
            'language': language,
            'previewOnly': preview_only
        })
        return success(data=result)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(method='put', operation_summary='更新图像')
@api_view(['PUT'])
def update_image(request, project_id, image_id):
    _ensure_project(project_id)
    try:
        image = get_object_or_404(Image, id=image_id, project_id=project_id)
        image.note = request.data.get('note', image.note)
        image.image_name = request.data.get('imageName', image.image_name)
        image.save()
        return success(data={'id': str(image.id), 'updated': True})
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

