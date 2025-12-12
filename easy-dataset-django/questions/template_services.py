"""
问题模板服务
处理基于模板为数据源批量生成问题的逻辑
"""
from typing import Dict, List
from nanoid import generate
import logging

from .models import Question, QuestionTemplate
from chunks.models import Chunk
from images.models import Image
from projects.models import Project

logger = logging.getLogger(__name__)


def get_image_chunk(project: Project) -> Chunk:
    """获取或创建图片专用的虚拟chunk"""
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
    
    return image_chunk


def generate_questions_for_text_chunks(project_id: str, template: QuestionTemplate, only_new: bool = False) -> Dict:
    """
    为所有文本块生成问题
    :param project_id: 项目ID
    :param template: 问题模板对象
    :param only_new: 是否只为新的数据源创建（编辑模式）
    :return: 生成结果
    """
    success_count = 0
    fail_count = 0
    errors = []
    
    try:
        # 获取项目下所有文本块（排除 Image Chunk 和 Distilled Content）
        chunks = Chunk.objects.filter(
            project_id=project_id
        ).exclude(
            name__in=['Image Chunk', 'Distilled Content']
        ).values('id')
        
        target_chunks = list(chunks)
        
        # 编辑模式：只为还未创建此模板问题的文本块创建
        if only_new and template.id:
            target_chunks = []
            for chunk in chunks:
                existing_question = Question.objects.filter(
                    project_id=project_id,
                    chunk_id=chunk['id'],
                    template_id=template.id
                ).first()
                if not existing_question:
                    target_chunks.append(chunk)
        
        # 为每个文本块创建问题
        if target_chunks:
            questions_to_create = []
            for chunk in target_chunks:
                questions_to_create.append(
                    Question(
                        id=generate(size=12),
                        project_id=project_id,
                        chunk_id=chunk['id'],
                        question=template.question,
                        template_id=template.id,
                        label='',
                        answered=False
                    )
                )
            
            # 批量创建问题
            Question.objects.bulk_create(questions_to_create)
            success_count = len(questions_to_create)
        
        return {'successCount': success_count, 'failCount': fail_count, 'errors': errors}
    except Exception as error:
        logger.error(f'获取文本块失败: {error}')
        return {
            'successCount': success_count,
            'failCount': fail_count,
            'errors': errors + [f'获取文本块失败: {str(error)}']
        }


def generate_questions_for_images(project_id: str, template: QuestionTemplate, only_new: bool = False) -> Dict:
    """
    为所有图片生成问题
    :param project_id: 项目ID
    :param template: 问题模板对象
    :param only_new: 是否只为新的数据源创建（编辑模式）
    :return: 生成结果
    """
    success_count = 0
    fail_count = 0
    errors = []
    
    try:
        # 获取项目下所有图片
        images = Image.objects.filter(project_id=project_id).values('id', 'image_name')
        
        # 获取或创建图片专用的虚拟chunk
        project = Project.objects.get(id=project_id)
        image_chunk = get_image_chunk(project)
        
        # 为每个图片创建问题
        for image in images:
            try:
                # 编辑模式：检查是否已经创建过此模板的问题
                if only_new and template.id:
                    existing_question = Question.objects.filter(
                        project_id=project_id,
                        image_id=image['id'],
                        template_id=template.id
                    ).first()
                    if existing_question:
                        continue  # 跳过已存在的
                
                # 创建图片问题
                Question.objects.create(
                    id=generate(size=12),
                    project_id=project_id,
                    chunk=image_chunk,
                    question=template.question,
                    image_id=image['id'],
                    image_name=image.get('image_name', ''),
                    template_id=template.id,
                    label='image',
                    answered=False
                )
                success_count += 1
            except Exception as error:
                logger.error(f'为图片 {image["id"]} 创建问题失败: {error}')
                fail_count += 1
                errors.append(f'图片 {image.get("image_name", image["id"])}: {str(error)}')
        
        return {'successCount': success_count, 'failCount': fail_count, 'errors': errors}
    except Exception as error:
        logger.error(f'获取图片失败: {error}')
        return {
            'successCount': success_count,
            'failCount': fail_count,
            'errors': errors + [f'获取图片失败: {str(error)}']
        }


def generate_questions_from_template(project_id: str, template: QuestionTemplate) -> Dict:
    """
    根据问题模板为所有相关数据源创建问题
    :param project_id: 项目ID
    :param template: 问题模板对象
    :return: 生成结果统计
    """
    source_type = template.source_type
    success_count = 0
    fail_count = 0
    errors = []
    
    try:
        if source_type == 'text':
            # 为所有文本块生成问题
            result = generate_questions_for_text_chunks(project_id, template)
            success_count += result['successCount']
            fail_count += result['failCount']
            errors.extend(result['errors'])
        elif source_type == 'image':
            # 为所有图片生成问题
            result = generate_questions_for_images(project_id, template)
            success_count += result['successCount']
            fail_count += result['failCount']
            errors.extend(result['errors'])
        
        return {
            'success': True,
            'successCount': success_count,
            'failCount': fail_count,
            'errors': errors,
            'message': f'成功为 {success_count} 个数据源创建问题，{fail_count} 个失败'
        }
    except Exception as error:
        logger.error(f'生成问题失败: {error}')
        return {
            'success': False,
            'successCount': success_count,
            'failCount': fail_count,
            'errors': errors + [str(error)],
            'message': '生成问题过程中发生错误'
        }


def generate_questions_from_template_edit(project_id: str, template: QuestionTemplate) -> Dict:
    """
    编辑模式：为还未创建此模板问题的数据源生成问题
    :param project_id: 项目ID
    :param template: 问题模板对象
    :return: 生成结果统计
    """
    source_type = template.source_type
    success_count = 0
    fail_count = 0
    errors = []
    
    try:
        if source_type == 'text':
            result = generate_questions_for_text_chunks(project_id, template, only_new=True)
            success_count += result['successCount']
            fail_count += result['failCount']
            errors.extend(result['errors'])
        elif source_type == 'image':
            result = generate_questions_for_images(project_id, template, only_new=True)
            success_count += result['successCount']
            fail_count += result['failCount']
            errors.extend(result['errors'])
        
        return {
            'success': True,
            'successCount': success_count,
            'failCount': fail_count,
            'errors': errors,
            'message': f'成功为 {success_count} 个数据源创建问题，{fail_count} 个失败'
        }
    except Exception as error:
        logger.error(f'生成问题失败: {error}')
        return {
            'success': False,
            'successCount': success_count,
            'failCount': fail_count,
            'errors': errors + [str(error)],
            'message': '生成问题过程中发生错误'
        }


def check_template_generation_availability(project_id: str, source_type: str) -> Dict:
    """
    检查模板是否可以生成问题
    :param project_id: 项目ID
    :param source_type: 数据源类型
    :return: 检查结果
    """
    try:
        count = 0
        
        if source_type == 'text':
            # 获取文本块数量（排除 Image Chunk 和 Distilled Content）
            count = Chunk.objects.filter(
                project_id=project_id
            ).exclude(
                name__in=['Image Chunk', 'Distilled Content']
            ).count()
        elif source_type == 'image':
            # 获取图片数量
            count = Image.objects.filter(project_id=project_id).count()
        
        source_name = '文本块' if source_type == 'text' else '图片'
        
        return {
            'available': count > 0,
            'count': count,
            'message': (
                f'找到 {count} 个{source_name}，可以生成问题'
                if count > 0
                else f'项目中没有{source_name}，无法生成问题'
            )
        }
    except Exception as error:
        logger.error(f'检查数据源可用性失败: {error}')
        return {
            'available': False,
            'count': 0,
            'message': '检查数据源时发生错误'
        }

