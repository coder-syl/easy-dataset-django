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
from common.services.prompt_service import get_answer_prompt
from nanoid import generate


def import_images_from_directories(project_id: str, directories: List[str]) -> Dict:
    """
    从目录导入图片
    :param project_id: 项目ID
    :param directories: 目录列表
    :return: 导入结果
    """
    project = Project.objects.get(id=project_id)
    project_path = Path('local-db') / project_id / 'images'
    project_path.mkdir(parents=True, exist_ok=True)
    
    imported_images = []
    supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
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
                
                # 创建图片记录
                image = Image.objects.create(
                    id=generate(size=12),
                    project=project,
                    image_name=image_file.name,
                    image_ext=image_file.suffix,
                    path=str(project_path),
                    size=file_size
                )
                
                imported_images.append({
                    'id': image.id,
                    'imageName': image.image_name,
                    'size': image.size
                })
            except Exception as e:
                continue
    
    return {
        'success': True,
        'imported': len(imported_images),
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
    if language == 'en':
        prompt = f"""Analyze the following image and generate {count} questions about it.

Please generate questions in JSON array format:
["Question 1", "Question 2", ...]

Generate {count} questions:"""
    else:
        prompt = f"""分析以下图片并生成{count}个相关问题。

请以JSON数组格式生成问题：
["问题1", "问题2", ...]

生成{count}个问题："""
    
    # 调用视觉模型生成问题（简化版本，使用文本模型）
    # TODO: 集成真正的视觉模型API
    response = llm_service.get_response_with_cot(prompt)
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


def generate_dataset_for_image(project_id: str, image_id: str, question: str, 
                                options: Dict) -> Dict:
    """
    为指定图片生成数据集（问答对）
    :param project_id: 项目ID
    :param image_id: 图片ID
    :param question: 问题
    :param options: 选项，包含model, language, previewOnly
    :return: 生成结果
    """
    model = options.get('model')
    language = options.get('language', 'zh')
    preview_only = options.get('previewOnly', False)
    
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
    
    # 创建LLM服务
    llm_service = LLMService(model)
    
    # 构建答案生成提示词
    prompt = get_answer_prompt(language, f'[Image: {image.image_name}]', question, project_id)
    
    # 调用视觉模型生成答案（简化版本）
    # TODO: 集成真正的视觉模型API
    response = llm_service.get_response_with_cot(prompt)
    answer = response.get('answer', '')
    
    if preview_only:
        return {
            'answer': answer,
            'dataset': None
        }
    
    # 创建数据集
    dataset = ImageDataset.objects.create(
        id=generate(size=12),
        project_id=project_id,
        image_id=image.id,
        image_name=image.image_name,
        question=question,
        answer=answer,
        confirmed=False
    )
    
    return {
        'answer': answer,
        'dataset': {
            'id': dataset.id,
            'question': dataset.question,
            'answer': dataset.answer
        }
    }


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
