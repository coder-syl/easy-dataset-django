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
    from PIL import Image as PILImage
    import io
    
    project = Project.objects.get(id=project_id)
    images_dir = Path('local-db') / project_id / 'images'
    images_dir.mkdir(parents=True, exist_ok=True)
    dest = images_dir / file_name
    with open(dest, 'wb') as f:
        f.write(data)
        
    # 获取图片尺寸
    width, height = None, None
    try:
        with PILImage.open(io.BytesIO(data)) as img:
            width, height = img.size
    except Exception as e:
        print(f"Warning: Could not get dimensions for {file_name}: {e}")
        
    img = Image.objects.create(
        id=generate(size=12),
        project=project,
        image_name=file_name,
        path=str(images_dir),
        size=len(data),
        width=width,
        height=height
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
    zip_name = None
    
    # 1) 若有zip文件
    if request.FILES:
        up_file = next(iter(request.FILES.values()))
        zip_name = up_file.name
        
        if not zip_name.lower().endswith('.zip'):
            return error(message='只支持 ZIP 格式的压缩包', response_status=status.HTTP_400_BAD_REQUEST)
        
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
            # 添加 zipName 字段
            result['zipName'] = zip_name
            return success(data=result)
    
    # 2) directories列表
    directories = request.data.get('directories', [])
    result = import_images_from_directories(project_id, directories)
    return success(data=result)


@swagger_auto_schema(method='post', operation_summary='PDF转图像')
@api_view(['POST'])
def pdf_convert(request, project_id):
    """将PDF页面转为图片并入库（支持 FormData 文件上传）"""
    _ensure_project(project_id)
    pdf_name = None
    
    # 优先处理 FormData 文件上传（与 Node.js 一致）
    if request.FILES:
        pdf_file = next(iter(request.FILES.values()))
        pdf_name = pdf_file.name
        
        if not pdf_name.lower().endswith('.pdf'):
            return error(message='只支持 PDF 文件', response_status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 读取 PDF 文件
            pdf_bytes = pdf_file.read()
            
            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path = Path(tmpdir) / pdf_name
                pdf_path.write_bytes(pdf_bytes)
                doc = fitz.open(pdf_path)
                saved = []
                for i, page in enumerate(doc):
                    pix = page.get_pixmap()
                    img_name = f"{Path(pdf_name).stem}_p{i+1}.png"
                    img_bytes = pix.tobytes("png")
                    img = _save_image_file(project_id, img_name, img_bytes)
                    saved.append({'id': str(img.id), 'fileName': img.image_name})
                doc.close()
            
            return success(data={
                'success': True,
                'count': len(saved),
                'images': saved,
                'pdfName': pdf_name
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 兼容旧版本：base64 编码方式
    file_name = request.data.get('fileName') or 'document.pdf'
    pdf_base64 = request.data.get('pdfBase64')
    if not pdf_base64:
        return error(message='缺少 PDF 文件或 pdfBase64', response_status=status.HTTP_400_BAD_REQUEST)
    
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
    """获取下一个含有未回答问题的图像（返回完整图片详情）"""
    _ensure_project(project_id)
    from questions.models import Question
    from .services import getImageDetailWithQuestions
    
    # 查找含有未回答问题的图片 ID
    unanswered_question = Question.objects.filter(
        project_id=project_id,
        answered=False,
        image_id__isnull=False
    ).first()
    
    if not unanswered_question:
        # 如果没有未回答的问题，返回 null
        return success(data=None)
        
    # 获取对应的图片详情（包含问题列表和已标注数据）
    try:
        image_data = getImageDetailWithQuestions(project_id, unanswered_question.image_id)
        return success(data=image_data)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(method='post', operation_summary='创建图像标注')
@api_view(['POST'])
def annotations(request, project_id):
    """创建图像标注（创建 ImageDataset 并更新 Question.answered）"""
    _ensure_project(project_id)
    
    image_id = request.data.get('imageId')
    image_name = request.data.get('imageName')
    question_id = request.data.get('questionId')
    question = request.data.get('question')
    answer_type = request.data.get('answerType', 'text')
    answer = request.data.get('answer')
    note = request.data.get('note', '')
    
    # 验证必填字段
    if not image_id or not question or not answer_type or answer is None:
        return error(message='缺少必要参数：imageId, question, answerType, answer', 
                    response_status=status.HTTP_400_BAD_REQUEST)
    
    # 验证答案类型
    if answer_type not in ['text', 'label', 'custom_format']:
        return error(message='无效的答案类型', response_status=status.HTTP_400_BAD_REQUEST)
    
    # 验证答案内容
    if answer_type == 'text' and not isinstance(answer, str):
        return error(message='文本类型答案必须是字符串', response_status=status.HTTP_400_BAD_REQUEST)
    if answer_type == 'label' and not isinstance(answer, list):
        return error(message='标签类型答案必须是数组', response_status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 验证图片存在
        image = Image.objects.get(id=image_id, project_id=project_id)
        
        # 验证问题存在
        from questions.models import Question
        if question_id:
            question_record = Question.objects.filter(id=question_id, project_id=project_id, image_id=image_id).first()
            if not question_record:
                return error(message='问题不存在', response_status=status.HTTP_404_NOT_FOUND)
        else:
            # 如果没有 questionId，尝试通过 question 文本查找
            question_record = Question.objects.filter(
                project_id=project_id, 
                image_id=image_id, 
                question=question
            ).first()
            if not question_record:
                return error(message='问题不存在，请先创建问题', response_status=status.HTTP_404_NOT_FOUND)
        
        # 序列化答案
        answer_string = answer
        if answer_type != 'text' and not isinstance(answer_string, str):
            import json
            answer_string = json.dumps(answer, ensure_ascii=False)
        
        # 创建 ImageDataset 记录
        from image_datasets.models import ImageDataset
        dataset = ImageDataset.objects.create(
            id=generate(size=12),
            project_id=project_id,
            image_id=image.id,
            image_name=image_name or image.image_name,
            question_id=question_record.id,
            question=question,
            answer=answer_string,
            answer_type=answer_type,
            model='manual',
            note=note
        )
        
        # 更新问题的 answered 状态
        question_record.answered = True
        question_record.save()
        
        return success(data={
            'success': True,
            'dataset': {
                'id': dataset.id,
                'question': dataset.question,
                'answer': dataset.answer
            },
            'questionId': question_record.id
        })
    except Image.DoesNotExist:
        return error(message='图片不存在', response_status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(method='post', operation_summary='生成图像问题')
@api_view(['POST'])
def generate_questions(request, project_id):
    _ensure_project(project_id)
    image_id = request.data.get('imageId')
    image_name = request.data.get('imageName')  # 支持通过 imageName 查找
    model = request.data.get('model')
    language = request.data.get('language', 'zh')
    count = request.data.get('count', 3)
    
    # 如果提供了 imageName，通过 imageName 查找 imageId
    if image_name and not image_id:
        try:
            image = Image.objects.get(project_id=project_id, image_name=image_name)
            image_id = image.id
        except Image.DoesNotExist:
            return error(message='图片不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if not image_id or not model:
        return error(message='imageId/imageName 和 model 必填', response_status=status.HTTP_400_BAD_REQUEST)
    
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
    image_name = request.data.get('imageName')  # 支持通过 imageName 查找
    question = request.data.get('question')
    model = request.data.get('model')
    language = request.data.get('language', 'zh')
    preview_only = request.data.get('previewOnly', False)
    
    # 如果提供了 imageName，通过 imageName 查找 imageId
    if image_name and not image_id:
        try:
            image = Image.objects.get(project_id=project_id, image_name=image_name)
            image_id = image.id
        except Image.DoesNotExist:
            return error(message='图片不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if not all([image_id, question, model]):
        return error(message='imageId/imageName, question, model 不能为空', response_status=status.HTTP_400_BAD_REQUEST)
    
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

