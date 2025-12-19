"""
图像服务
处理图像相关业务逻辑
"""
from typing import Dict, Optional, List
from pathlib import Path
import base64
import shutil

from .models import Image
from projects.models import Project
from questions.models import Question
from image_datasets.models import ImageDataset
from chunks.models import Chunk
from common.services.llm_service import LLMService
from common.services.prompt_service import get_image_question_prompt, get_image_answer_prompt
from nanoid import generate


def import_images_from_directories(project_id: str, directories: List[str]) -> Dict:
    """
    从目录导入图片
    :param project_id: 项目ID
    :param directories: 目录列表
    :return: 导入结果
    """
    from PIL import Image as PILImage
    
    project = Project.objects.get(id=project_id)
    project_path = Path('local-db') / project_id / 'images'
    project_path.mkdir(parents=True, exist_ok=True)
    
    imported_images = []
    supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            continue
        
        # 遍历目录中的图片文件
        for image_file in dir_path.iterdir():
            if image_file.suffix.lower() not in supported_formats:
                continue
            
            try:
                # 复制文件到项目目录
                dest_path = project_path / image_file.name
                shutil.copy2(image_file, dest_path)
                
                # 获取文件信息
                file_size = dest_path.stat().st_size
                width, height = None, None
                
                # 获取图片尺寸
                if image_file.suffix.lower() != '.svg':
                    try:
                        with PILImage.open(dest_path) as img:
                            width, height = img.size
                    except Exception as e:
                        print(f"Warning: Could not get dimensions for {image_file.name}: {e}")
                
                # 检查记录是否已存在
                image_record = Image.objects.filter(
                    project=project,
                    image_name=image_file.name
                ).first()
                
                if image_record:
                    # 更新现有记录
                    image_record.size = file_size
                    image_record.width = width
                    image_record.height = height
                    image_record.path = str(project_path)
                    image_record.save()
                else:
                    # 创建新记录
                    image_record = Image.objects.create(
                        id=generate(size=12),
                        project=project,
                        image_name=image_file.name,
                        path=str(project_path),
                        size=file_size,
                        width=width,
                        height=height
                    )
                
                imported_images.append({
                    'id': image_record.id,
                    'imageName': image_record.image_name,
                    'size': image_record.size,
                    'width': image_record.width,
                    'height': image_record.height
                })
            except Exception as e:
                print(f"Error importing {image_file.name}: {e}")
                continue
    
    return {
        'success': True,
        'count': len(imported_images),
        'images': imported_images
    }


def generate_questions_for_image(project_id: str, image_id: str, options: Dict) -> Dict:
    """
    为指定图片生成问题
    :param project_id: 项目ID
    :param image_id: 图片ID
    :param options: 选项，包含model, language, count
    :return: 生成结果
    """
    model = options.get('model')
    language = options.get('language', 'zh')
    count = options.get('count', 3)
    
    if not model:
        raise ValueError('模型配置不能为空')
    
    # 获取图片信息
    image = Image.objects.get(id=image_id, project_id=project_id)
    
    # 读取图片文件
    project_path = Path('local-db') / project_id / 'images'
    image_path = project_path / image.image_name
    
    if not image_path.exists():
        raise ValueError(f'图片文件 {image.image_name} 不存在')
    
    with open(image_path, 'rb') as f:
        image_buffer = f.read()
    
    base64_image = base64.b64encode(image_buffer).decode('utf-8')
    mime_type = get_mime_type(image.image_name)
    
    # 创建LLM服务
    llm_service = LLMService(model)
    
    # 构建问题生成提示词
    prompt = get_image_question_prompt(language, count, project_id)
    
    # 调用视觉模型生成问题
    response = llm_service.get_vision_response(prompt, base64_image, mime_type)
    answer = response.get('answer', '')
    
    # 解析问题列表
    questions = parse_questions_from_response(answer)
    
    if not questions or len(questions) == 0:
        raise ValueError('生成问题失败或问题列表为空')
    
    # 获取或创建图片专用的虚拟chunk
    project = Project.objects.get(id=project_id)
    image_chunk = Chunk.objects.filter(
        project=project,
        name='Image Chunk'
    ).first()
    
    if not image_chunk:
        image_chunk = Chunk.objects.create(
            project=project,
            name='Image Chunk',
            file_id='image',
            file_name='image.md',
            content='This text block is used to store questions generated from images.',
            summary='Image questions',
            size=0
        )
    
    # 保存问题
    saved_questions = []
    for question_text in questions:
        question = Question.objects.create(
            id=generate(size=12),
            project=project,
            chunk=image_chunk,
            question=question_text,
            label='image',
            image_id=image.id,
            image_name=image.image_name,
            answered=False
        )
        saved_questions.append({
            'id': question.id,
            'question': question.question
        })
    
    return {
        'imageId': image.id,
        'imageName': image.image_name,
        'questions': [q['question'] for q in saved_questions],
        'total': len(saved_questions)
    }


def generate_dataset_for_image(project_id: str, image_id: str, question: any, 
                                options: Dict) -> Dict:
    """
    为指定图片生成数据集（问答对）
    :param project_id: 项目ID
    :param image_id: 图片ID
    :param question: 问题 (可以是字符串或字典 {"id": ..., "question": ...})
    :param options: 选项，包含model, language, previewOnly
    :return: 生成结果
    """
    model = options.get('model')
    language = options.get('language', 'zh')
    preview_only = options.get('previewOnly', False)
    
    if not model:
        raise ValueError('模型配置不能为空')
    
    # 解析问题
    question_id = None
    question_text = ""
    if isinstance(question, dict):
        question_id = question.get('id')
        question_text = question.get('question', '')
    else:
        question_text = str(question)
        
    # 获取图片信息
    image = Image.objects.get(id=image_id, project_id=project_id)
    
    # 读取图片文件
    project_path = Path('local-db') / project_id / 'images'
    image_path = project_path / image.image_name
    
    if not image_path.exists():
        raise ValueError(f'图片文件 {image.image_name} 不存在')
    
    with open(image_path, 'rb') as f:
        image_buffer = f.read()
    
    base64_image = base64.b64encode(image_buffer).decode('utf-8')
    mime_type = get_mime_type(image.image_name)
    
    # 获取问题模板
    from questions.models import QuestionTemplate
    question_template = {'answerType': 'text'}
    if question_id:
        try:
            template = QuestionTemplate.objects.get(id=question_id)
            question_template = {
                'answerType': template.answer_type,
                'labels': template.labels,
                'customFormat': template.custom_format
            }
        except QuestionTemplate.DoesNotExist:
            pass
            
    # 创建LLM服务
    llm_service = LLMService(model)
    
    # 构建答案生成提示词
    prompt = get_image_answer_prompt(language, question_text, question_template, project_id)
    
    # 调用视觉模型生成答案
    response = llm_service.get_vision_response(prompt, base64_image, mime_type)
    answer = response.get('answer', '')
    
    if preview_only:
        return {
            'imageId': image.id,
            'imageName': image.image_name,
            'question': question_text,
            'answer': answer,
            'dataset': None
        }
    
    # 创建数据集
    dataset = ImageDataset.objects.create(
        id=generate(size=12),
        project_id=project_id,
        image_id=image.id,
        image_name=image.image_name,
        question=question_text,
        question_id=question_id,
        answer=answer,
        answer_type=question_template.get('answerType', 'text'),
        model=model.get('modelId') or model.get('modelName', 'unknown'),
        confirmed=False
    )
    
    # 更新对应问题的 answered 状态
    Question.objects.filter(
        project_id=project_id,
        image_id=image.id,
        question=question_text
    ).update(answered=True)
    
    return {
        'imageId': image.id,
        'imageName': image.image_name,
        'question': question_text,
        'answer': answer,
        'dataset': {
            'id': dataset.id,
            'question': dataset.question,
            'answer': dataset.answer
        }
    }


def getImageDetailWithQuestions(project_id: str, image_id: str) -> Dict:
    """
    获取图片详情（包含问题列表和已标注数据）
    :param project_id: 项目ID
    :param image_id: 图片ID
    :return: 图片详情
    """
    try:
        # 获取图片基本信息
        image = Image.objects.get(id=image_id, project_id=project_id)
        
        # 获取图片的所有问题
        questions = Question.objects.filter(
            project_id=project_id,
            image_id=image.id
        ).order_by('-create_at')
        
        # 获取关联的模板 ID
        template_ids = [q.template_id for q in questions if q.template_id]
        
        # 获取关联的模板
        from questions.models import QuestionTemplate
        templates = QuestionTemplate.objects.filter(id__in=template_ids) if template_ids else []
        template_map = {str(t.id): t for t in templates}
        
        # 获取每个问题的已标注答案
        questions_with_answers = []
        for question in questions:
            # 查找该问题的已标注答案
            existing_answer = ImageDataset.objects.filter(
                image_id=image.id,
                question=question.question
            ).order_by('-create_at').first()
            
            # 获取关联的模板
            template = template_map.get(str(question.template_id)) if question.template_id else None
            
            questions_with_answers.append({
                'id': question.id,
                'question': question.question,
                'templateId': question.template_id,
                'template': template,
                'hasAnswer': existing_answer is not None,
                'answer': existing_answer.answer if existing_answer else None,
                'answerId': existing_answer.id if existing_answer else None
            })
        
        # 分离已标注和未标注的问题
        answered_questions = []
        unanswered_questions = []
        
        for q in questions_with_answers:
            q_data = {
                'id': q['id'],
                'question': q['question'],
                'answerType': q['template'].answer_type if q['template'] else 'text',
                'labels': q['template'].labels if q['template'] else '',
                'customFormat': q['template'].custom_format if q['template'] else '',
                'description': q['template'].description if q['template'] else '',
                'templateId': q['templateId']
            }
            
            if q['hasAnswer']:
                q_data['answer'] = q['answer']
                q_data['answerId'] = q['answerId']
                answered_questions.append(q_data)
            else:
                unanswered_questions.append(q_data)
        
        # 获取图片 base64
        from .views import get_image_base64
        base64_image = get_image_base64(project_id, image.image_name)
        
        return {
            'id': image.id,
            'imageName': image.image_name,
            'path': image.path,
            'size': image.size,
            'width': image.width,
            'height': image.height,
            'createAt': image.create_at,
            'updateAt': image.update_at,
            'base64': base64_image,
            'format': Path(image.image_name).suffix.lower().replace('.', ''),
            'answeredQuestions': answered_questions,
            'unansweredQuestions': unanswered_questions,
            'datasetCount': len(answered_questions),
            'questionCount': len(questions)
        }
    except Exception as e:
        print(f"Error in getImageDetailWithQuestions: {str(e)}")
        raise e


def get_mime_type(image_name: str) -> str:
    """获取图片MIME类型"""
    ext = Path(image_name).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


def parse_questions_from_response(response: str) -> list:
    """从LLM响应中解析问题列表"""
    import json
    import re
    
    try:
        # 尝试直接解析JSON
        questions = json.loads(response)
        if isinstance(questions, list):
            return questions
    except:
        pass
    
    # 尝试提取JSON数组
    json_match = re.search(r'\[.*?\]', response, re.DOTALL)
    if json_match:
        try:
            questions = json.loads(json_match.group())
            if isinstance(questions, list):
                return questions
        except:
            pass
    
    # 尝试提取引号中的内容
    questions = re.findall(r'"([^"]+)"', response)
    if questions:
        return questions
    
    # 如果都失败，按行分割
    lines = response.split('\n')
    questions = [line.strip('- ').strip() for line in lines if line.strip() and '?' in line]
    return questions[:10]  # 最多返回10个
