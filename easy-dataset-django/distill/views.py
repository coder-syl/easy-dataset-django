"""
数据蒸馏视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from nanoid import generate
import json

from projects.models import Project
from tags.models import Tag
from chunks.models import Chunk
from questions.models import Question
from common.response.result import success, error
from common.services.llm_service import LLMService
from questions.services import parse_questions_from_response


@swagger_auto_schema(
    method='post',
    operation_summary='蒸馏问题',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'tagPath': openapi.Schema(type=openapi.TYPE_STRING),
            'currentTag': openapi.Schema(type=openapi.TYPE_STRING),
            'tagId': openapi.Schema(type=openapi.TYPE_STRING),
            'count': openapi.Schema(type=openapi.TYPE_INTEGER),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('生成的问题列表')}
)
@api_view(['POST'])
def distill_questions(request, project_id):
    """蒸馏问题"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        tag_path = request.data.get('tagPath')
        current_tag = request.data.get('currentTag')
        tag_id = request.data.get('tagId')
        count = request.data.get('count', 5)
        model = request.data.get('model')
        language = request.data.get('language', 'zh')
        
        if not current_tag or not tag_path:
            error_msg = 'Tag information cannot be empty' if language == 'en' else '标签信息不能为空'
            return error(message=error_msg, response_status=status.HTTP_400_BAD_REQUEST)
        
        # 获取或创建蒸馏文本块
        distill_chunk = Chunk.objects.filter(
            project=project,
            name='Distilled Content'
        ).first()
        
        if not distill_chunk:
            distill_chunk = Chunk.objects.create(
                id=generate(size=12),
                project=project,
                file_id='distilled',
                file_name='distilled.md',
                name='Distilled Content',
                content='This text block is used to store questions generated through data distillation and is not related to actual literature.',
                summary='Questions generated through data distillation',
                size=0
            )
        
        # 获取已有的问题，避免重复
        existing_questions = Question.objects.filter(
            project=project,
            label=current_tag,
            chunk=distill_chunk
        ).values_list('question', flat=True)
        
        existing_question_texts = list(existing_questions)
        
        # 调用LLM生成问题
        llm_service = LLMService(model)
        
        # 构建提示词
        prompt = f"""根据标签路径和当前标签，生成{count}个相关问题。

标签路径：{tag_path}
当前标签：{current_tag}
已有问题：{json.dumps(existing_question_texts, ensure_ascii=False)}

请以JSON数组格式生成问题：
["问题1", "问题2", ...]

生成{count}个问题："""
        
        response = llm_service.get_response_with_cot(prompt)
        answer = response.get('answer', '')
        
        # 解析问题
        questions = parse_questions_from_response(answer)
        
        # 保存问题
        saved_questions = []
        for question_text in questions:
            question = Question.objects.create(
                id=generate(size=12),
                project=project,
                question=question_text,
                label=current_tag,
                chunk=distill_chunk,
                answered=False
            )
            saved_questions.append({
                'id': question.id,
                'question': question.question,
                'label': question.label
            })
        
        return success(data=saved_questions)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='根据标签ID获取问题列表',
    manual_parameters=[
        openapi.Parameter('tagId', openapi.IN_QUERY, description='标签ID', type=openapi.TYPE_STRING, required=True),
    ],
    responses={200: openapi.Response('问题列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='按标签蒸馏问题',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'tagName': openapi.Schema(type=openapi.TYPE_STRING),
            'count': openapi.Schema(type=openapi.TYPE_INTEGER),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('生成的问题列表')}
)
@api_view(['GET', 'POST'])
def distill_questions_by_tag(request, project_id):
    """根据标签ID获取问题列表或按标签蒸馏问题"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # GET 方法：根据标签ID获取问题列表（与 Node.js 一致）
        try:
            tag_id = request.GET.get('tagId')
            
            if not tag_id:
                return error(message='标签ID不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 获取标签信息
            tag = Tag.objects.filter(id=tag_id, project=project).first()
            if not tag:
                return error(message='标签不存在', response_status=status.HTTP_404_NOT_FOUND)
            
            # 获取或创建蒸馏文本块
            distill_chunk = Chunk.objects.filter(
                project=project,
                name='Distilled Content'
            ).first()
            
            if not distill_chunk:
                distill_chunk = Chunk.objects.create(
                    id=generate(size=12),
                    project=project,
                    file_id='distilled',
                    file_name='distilled.md',
                    name='Distilled Content',
                    content='This text block is used to store questions generated through data distillation and is not related to actual literature.',
                    summary='Questions generated through data distillation',
                    size=0
                )
            
            # 调试信息：检查查询条件
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'查询问题 - 项目ID: {project_id}, 标签ID: {tag_id}, 标签Label: "{tag.label}", 蒸馏Chunk ID: {distill_chunk.id}')
            
            # 先检查是否有匹配label的问题（不限制chunk）
            all_label_questions = Question.objects.filter(
                project=project,
                label=tag.label
            )
            all_label_count = all_label_questions.count()
            logger.info(f'项目中标签为 "{tag.label}" 的问题总数: {all_label_count}')
            
            # 检查这些问题的chunk信息
            if all_label_count > 0:
                for q in all_label_questions[:5]:  # 只检查前5个
                    logger.info(f'问题ID: {q.id}, Label: "{q.label}", Chunk ID: {q.chunk_id}, Chunk Name: {q.chunk.name if q.chunk else "None"}')
            
            # 检查所有名为 'Distilled Content' 的chunk
            all_distill_chunks = Chunk.objects.filter(
                project=project,
                name='Distilled Content'
            )
            distill_chunks_count = all_distill_chunks.count()
            logger.info(f'项目中名为 "Distilled Content" 的Chunk数量: {distill_chunks_count}')
            if distill_chunks_count > 1:
                logger.warning(f'发现多个 "Distilled Content" Chunk，这可能导致查询不到问题！')
                for dc in all_distill_chunks:
                    dc_questions_count = Question.objects.filter(
                        project=project,
                        label=tag.label,
                        chunk_id=dc.id
                    ).count()
                    logger.info(f'Chunk ID: {dc.id}, 匹配的问题数量: {dc_questions_count}')
            
            # 获取问题列表：先尝试使用当前distill_chunk，如果找不到，则查找所有distill_chunk中的问题
            questions = Question.objects.filter(
                project=project,
                label=tag.label,
                chunk_id=distill_chunk.id
            ).order_by('-create_at')
            
            questions_count = questions.count()
            logger.info(f'使用Chunk ID {distill_chunk.id} 匹配的问题数量: {questions_count}')
            
            # 如果当前chunk中没有找到问题，尝试查找所有distill_chunk中的问题
            if questions_count == 0 and distill_chunks_count > 1:
                logger.info('当前chunk中没有找到问题，尝试查找所有distill_chunk中的问题')
                distill_chunk_ids = list(all_distill_chunks.values_list('id', flat=True))
                questions = Question.objects.filter(
                    project=project,
                    label=tag.label,
                    chunk_id__in=distill_chunk_ids
                ).order_by('-create_at')
                questions_count = questions.count()
                logger.info(f'在所有distill_chunk中找到的问题数量: {questions_count}')
            
            # 注意：与 Node.js 保持一致，数据蒸馏模块只返回蒸馏 chunk 中的问题
            # 不回退到任意 chunk，确保数据蒸馏和问题管理模块的问题一致
       
            # 手动序列化为与 Node.js 一致的格式（驼峰命名）
            questions_data = [
                {
                    'id': q.id,
                    'chunkId': q.chunk_id,
                    'chunkName': q.chunk.name if q.chunk else '',
                    'gaPairId': q.ga_pair_id if q.ga_pair_id else None,
                    'question': q.question,
                    'label': q.label,
                    'answered': q.answered,
                    'imageId': q.image_id if q.image_id else None,
                    'imageName': q.image_name if q.image_name else None,
                    'templateId': q.template_id if q.template_id else None,
                    'projectId': project_id,
                    'createAt': q.create_at.isoformat() if hasattr(q.create_at, 'isoformat') else str(q.create_at),
                    'updateAt': q.update_at.isoformat() if hasattr(q.update_at, 'isoformat') else str(q.update_at)
                }
                for q in questions
            ]
            # 与 Node.js 一致：直接返回数组，不使用 success() 包装
            from rest_framework.response import Response
            return Response(questions_data, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'查询问题失败: {str(e)}', exc_info=True)
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        # POST 方法：按标签蒸馏问题
        try:
            tag_name = request.data.get('tagName')
            count = request.data.get('count', 5)
            model = request.data.get('model')
            language = request.data.get('language', 'zh')
            
            if not tag_name:
                return error(message='标签名不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 获取标签路径
            tag = Tag.objects.filter(project=project, label=tag_name).first()
            if not tag:
                return error(message='标签不存在', response_status=status.HTTP_404_NOT_FOUND)
            
            # 构建标签路径
            tag_path = tag_name
            parent_id = tag.parent_id
            while parent_id:
                parent_tag = Tag.objects.filter(id=parent_id).first()
                if parent_tag:
                    tag_path = f"{parent_tag.label} > {tag_path}"
                    parent_id = parent_tag.parent_id
                else:
                    break
            
            # 调用蒸馏问题接口
            return distill_questions(request, project_id)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取可蒸馏标签',
    responses={200: openapi.Response('标签列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='蒸馏标签',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'parentTag': openapi.Schema(type=openapi.TYPE_STRING),
            'parentTagId': openapi.Schema(type=openapi.TYPE_STRING),
            'tagPath': openapi.Schema(type=openapi.TYPE_STRING),
            'count': openapi.Schema(type=openapi.TYPE_INTEGER),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('生成的标签列表')}
)
@api_view(['GET', 'POST'])
def distill_tags(request, project_id):
    """蒸馏标签"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            # 获取所有标签
            tags = Tag.objects.filter(project=project)
            tags_data = [{
                'id': tag.id,
                'label': tag.label,
                'parentId': tag.parent_id
            } for tag in tags]
            
            return success(data={'tags': tags_data})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            parent_tag = request.data.get('parentTag')
            parent_tag_id = request.data.get('parentTagId')
            tag_path = request.data.get('tagPath', '')
            count = request.data.get('count', 10)
            model = request.data.get('model')
            language = request.data.get('language', 'zh')
            
            if not parent_tag:
                error_msg = 'Topic tag name cannot be empty' if language == 'en' else '主题标签名称不能为空'
                return error(message=error_msg, response_status=status.HTTP_400_BAD_REQUEST)
            
            # 查询现有标签
            existing_tags = Tag.objects.filter(
                project=project,
                parent_id=parent_tag_id
            )
            existing_tag_names = [tag.label for tag in existing_tags]
            
            # 调用LLM生成标签
            llm_service = LLMService(model)
            
            prompt = f"""根据父标签和标签路径，生成{count}个子标签。

父标签：{parent_tag}
标签路径：{tag_path}
已有标签：{json.dumps(existing_tag_names, ensure_ascii=False)}

请以JSON数组格式生成标签：
["标签1", "标签2", ...]

生成{count}个标签："""
            
            response = llm_service.get_response_with_cot(prompt)
            answer = response.get('answer', '')
            
            # 解析标签
            tags = parse_questions_from_response(answer)  # 复用问题解析函数
            
            # 保存标签
            saved_tags = []
            for tag_name in tags:
                tag = Tag.objects.create(
                    id=generate(size=12),
                    project=project,
                    label=tag_name,
                    parent_id=parent_tag_id
                )
                saved_tags.append({
                    'id': tag.id,
                    'label': tag.label,
                    'parentId': tag.parent_id
                })
            
            return success(data=saved_tags)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取项目的所有蒸馏标签',
    responses={200: openapi.Response('标签列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='蒸馏所有标签',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(type=openapi.TYPE_INTEGER),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('蒸馏结果')}
)
@api_view(['GET', 'POST'])
def distill_all_tags(request, project_id):
    """获取所有标签或蒸馏所有标签"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # GET 方法：获取项目的所有标签（与 Node.js 一致）
        try:
            tags = Tag.objects.filter(project=project).order_by('label')
            # 手动序列化为与 Node.js 一致的格式（驼峰命名）
            tags_data = [
                {
                    'id': tag.id,
                    'label': tag.label,
                    'parentId': tag.parent_id if tag.parent_id else None,
                    'projectId': project_id,
                }
                for tag in tags
            ]
            # 与 Node.js 一致：直接返回数组，不使用 success() 包装
            from rest_framework.response import Response
            return Response(tags_data, status=status.HTTP_200_OK)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        # POST 方法：蒸馏所有标签
        try:
            count = request.data.get('count', 10)
            model = request.data.get('model')
            language = request.data.get('language', 'zh')
            
            # 获取顶级标签
            top_tags = Tag.objects.filter(project=project, parent_id__isnull=True)
            
            results = []
            for top_tag in top_tags:
                # 为每个顶级标签生成子标签
                request.data['parentTag'] = top_tag.label
                request.data['parentTagId'] = top_tag.id
                request.data['tagPath'] = top_tag.label
                
                result = distill_tags(request, project_id)
                if result.status_code == 200:
                    results.append({
                        'parentTag': top_tag.label,
                        'success': True,
                        'tags': result.data.get('data', [])
                    })
            
            return success(data={'results': results})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='蒸馏指定标签',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(type=openapi.TYPE_INTEGER),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('蒸馏结果')}
)
@api_view(['POST'])
def distill_tag_by_id(request, project_id, tag_id):
    """蒸馏指定标签"""
    try:
        project = get_object_or_404(Project, id=project_id)
        tag = get_object_or_404(Tag, id=tag_id, project=project)
        
        count = request.data.get('count', 10)
        model = request.data.get('model')
        language = request.data.get('language', 'zh')
        
        # 构建标签路径
        tag_path = tag.label
        parent_id = tag.parent_id
        while parent_id:
            parent_tag = Tag.objects.filter(id=parent_id).first()
            if parent_tag:
                tag_path = f"{parent_tag.label} > {tag_path}"
                parent_id = parent_tag.parent_id
            else:
                break
        
        request.data['parentTag'] = tag.label
        request.data['parentTagId'] = tag.id
        request.data['tagPath'] = tag_path
        
        return distill_tags(request, project_id)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
