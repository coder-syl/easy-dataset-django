"""
问题管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
import json
import logging

from projects.models import Project
from chunks.models import Chunk

logger = logging.getLogger(__name__)
from .models import Question, QuestionTemplate
from .serializers import QuestionSerializer, QuestionCreateSerializer, QuestionTemplateSerializer
from .template_services import (
    generate_questions_from_template,
    generate_questions_from_template_edit,
    check_template_generation_availability
)
from common.response.result import success, error


@swagger_auto_schema(
    method='get',
    operation_summary='获取问题列表',
    responses={200: openapi.Response('问题列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='创建问题',
    request_body=QuestionCreateSerializer,
    responses={201: openapi.Response('创建成功')}
)
@api_view(['GET', 'POST'])
def question_list_create(request, project_id):
    """获取问题列表或创建问题"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            # 获取查询参数
            status_param = request.GET.get('status')
            answered = None
            if status_param == 'answered':
                answered = True
            elif status_param == 'unanswered':
                answered = False
            
            chunk_name = request.GET.get('chunkName')
            source_type = request.GET.get('source_type', 'all')  # 'all', 'text', 'image'
            selected_all = request.GET.get('selectedAll')
            get_all = request.GET.get('all')
            search_input = request.GET.get('input')
            image_id = request.GET.get('imageId')
            
            # 构建查询，按创建时间降序排序（最新的在第一页）
            queryset = Question.objects.filter(project=project).order_by('-create_at')
            
            # 过滤条件
            if answered is not None:
                queryset = queryset.filter(answered=answered)
            
            if chunk_name:
                queryset = queryset.filter(chunk__name=chunk_name)
            
            # 按图片ID过滤
            if image_id:
                queryset = queryset.filter(image_id=image_id)
            
            if source_type == 'text':
                queryset = queryset.filter(image_id__isnull=True)
            elif source_type == 'image':
                queryset = queryset.filter(image_id__isnull=False)
            
            if search_input:
                queryset = queryset.filter(question__icontains=search_input)
            
            # 如果只需要ID列表
            if selected_all:
                question_ids = queryset.values_list('id', flat=True)
                # 与 Node.js 保持一致：返回数组格式 [{id: '...'}, {id: '...'}]
                # Node.js 的 getQuestionsIds 返回 [{id: '...'}, {id: '...'}]
                # 前端期望 response.data 是数组，每个元素有 id 属性
                question_list = [{'id': str(qid)} for qid in question_ids]
                # 直接返回数组，不使用 success() 包装，与 Node.js 保持一致
                from rest_framework.response import Response
                return Response(question_list, status=status.HTTP_200_OK)
            
            # 如果需要所有数据
            if get_all:
                serializer = QuestionSerializer(queryset, many=True)
                return success(data=serializer.data)
            
            # 分页
            page = int(request.GET.get('page', 1))
            size = int(request.GET.get('size', 20))
            paginator = Paginator(queryset, size)
            page_obj = paginator.get_page(page)
            
            serializer = QuestionSerializer(page_obj.object_list, many=True)
            return success(data={
                'data': serializer.data,
                'total': paginator.count,
                'page': page,
                'size': size
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            serializer = QuestionCreateSerializer(data=request.data, context={'project': project})
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            # 设置项目ID
            serializer.validated_data['project'] = project
            question = serializer.save()
            
            result_serializer = QuestionSerializer(question)
            return success(data=result_serializer.data, response_status=status.HTTP_201_CREATED)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_templates_usage_count(template_ids):
    """批量获取模板使用统计"""
    from django.db.models import Count
    usage_counts = Question.objects.filter(template_id__in=template_ids).values('template_id').annotate(
        count=Count('id')
    )
    return {item['template_id']: item['count'] for item in usage_counts}


@swagger_auto_schema(
    method='get',
    operation_summary='获取问题模板列表',
    manual_parameters=[
        openapi.Parameter('source_type', openapi.IN_QUERY, description='数据源类型: text | image', type=openapi.TYPE_STRING),
        openapi.Parameter('search', openapi.IN_QUERY, description='按模板内容搜索', type=openapi.TYPE_STRING),
    ],
    responses={200: openapi.Response('模板列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='创建问题模板',
    request_body=QuestionTemplateSerializer,
    responses={201: openapi.Response('创建成功')}
)
@api_view(['GET', 'POST'])
def question_templates(request, project_id):
    """问题模板列表和创建（对齐 Node.js /questions/templates 接口）"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        try:
            source_type = request.GET.get('source_type')
            search = request.GET.get('search')

            queryset = QuestionTemplate.objects.filter(project=project)
            if source_type in ['text', 'image']:
                queryset = queryset.filter(source_type=source_type)
            if search:
                queryset = queryset.filter(question__icontains=search)

            templates = list(queryset.order_by('order', '-create_at'))

            # 获取使用统计
            template_ids = [tpl.id for tpl in templates]
            usage_counts = get_templates_usage_count(template_ids) if template_ids else {}

            # 使用序列化器返回数据（snake_case 格式）
            serializer = QuestionTemplateSerializer(templates, many=True)
            templates_data = serializer.data
            # 添加使用统计
            for idx, tpl_data in enumerate(templates_data):
                tpl_data['usage_count'] = usage_counts.get(templates[idx].id, 0)

            from rest_framework.response import Response
            return Response({'success': True, 'templates': templates_data}, status=status.HTTP_200_OK)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            serializer = QuestionTemplateSerializer(data=request.data, context={'project': project})
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            # 验证必填字段
            question = serializer.validated_data.get('question')
            source_type = serializer.validated_data.get('source_type')
            answer_type = serializer.validated_data.get('answer_type')
            
            if not question or not source_type or not answer_type:
                return error(message='缺少必要参数：question, source_type, answer_type', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 验证数据源类型
            if source_type not in ['image', 'text']:
                return error(message='无效的数据源类型', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 验证答案类型
            if answer_type not in ['text', 'label', 'custom_format']:
                return error(message='无效的答案类型', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 如果是标签类型，验证 labels
            if answer_type == 'label':
                labels = serializer.validated_data.get('labels', '')
                try:
                    labels_list = json.loads(labels) if isinstance(labels, str) else labels
                    if not labels_list or not isinstance(labels_list, list) or len(labels_list) == 0:
                        return error(message='标签类型问题必须提供标签列表', response_status=status.HTTP_400_BAD_REQUEST)
                except:
                    return error(message='标签类型问题必须提供标签列表', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 如果是自定义格式，验证 custom_format
            if answer_type == 'custom_format':
                custom_format = serializer.validated_data.get('custom_format', '')
                if not custom_format:
                    return error(message='自定义格式问题必须提供格式定义', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 设置项目
            serializer.validated_data['project'] = project
            template = serializer.save()
            
            # 序列化返回数据
            result_serializer = QuestionTemplateSerializer(template)
            result_data = result_serializer.data
            result_data['usage_count'] = 0  # 新创建的模板使用次数为 0
            
            # 如果 auto_generate 为 true，调用生成问题的逻辑
            generation_result = None
            auto_generate = request.data.get('auto_generate', False)
            if auto_generate:
                try:
                    # 先检查是否有可用的数据源
                    availability = check_template_generation_availability(project_id, template.source_type)
                    
                    if availability['available']:
                        generation_result = generate_questions_from_template(project_id, template)
                    else:
                        generation_result = {
                            'success': False,
                            'successCount': 0,
                            'failCount': 0,
                            'message': availability['message']
                        }
                except Exception as err:
                    logger.error(f'自动生成问题失败: {err}')
                    generation_result = {
                        'success': False,
                        'successCount': 0,
                        'failCount': 0,
                        'message': '自动生成问题时发生错误'
                    }
            
            from rest_framework.response import Response
            return Response({
                'success': True,
                'template': result_data,
                'generation': generation_result
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取单个问题模板',
    responses={200: openapi.Response('模板详情')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新问题模板',
    request_body=QuestionTemplateSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除问题模板',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'PUT', 'DELETE'])
def question_template_detail(request, project_id, template_id):
    """单个问题模板的获取、更新、删除（对齐 Node.js /questions/templates/{templateId} 接口）"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    try:
        template = QuestionTemplate.objects.get(id=template_id, project=project)
    except QuestionTemplate.DoesNotExist:
        return error(message='模板不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            # 获取使用统计
            usage_count = Question.objects.filter(template_id=template_id).count()
            
            serializer = QuestionTemplateSerializer(template)
            result_data = serializer.data
            result_data['usageCount'] = usage_count
            
            from rest_framework.response import Response
            return Response({'success': True, 'template': result_data}, status=status.HTTP_200_OK)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            serializer = QuestionTemplateSerializer(template, data=request.data, partial=True, context={'project': project})
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            # 验证数据源类型（如果提供）
            source_type = serializer.validated_data.get('source_type')
            if source_type and source_type not in ['image', 'text']:
                return error(message='无效的数据源类型', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 验证答案类型（如果提供）
            answer_type = serializer.validated_data.get('answer_type')
            if answer_type and answer_type not in ['text', 'label', 'custom_format']:
                return error(message='无效的答案类型', response_status=status.HTTP_400_BAD_REQUEST)
            
            template = serializer.save()
            
            # 序列化返回数据
            result_serializer = QuestionTemplateSerializer(template)
            result_data = result_serializer.data
            usage_count = Question.objects.filter(template_id=template_id).count()
            result_data['usage_count'] = usage_count
            
            # 如果 auto_generate 为 true，调用生成问题的逻辑
            generation_result = None
            auto_generate = request.data.get('auto_generate', False)
            if auto_generate:
                try:
                    generation_result = generate_questions_from_template_edit(project_id, template)
                except Exception as err:
                    logger.error(f'编辑模式自动生成问题失败: {err}')
                    generation_result = {
                        'success': False,
                        'successCount': 0,
                        'failCount': 0,
                        'message': '自动生成问题时发生错误'
                    }
            
            from rest_framework.response import Response
            return Response({
                'success': True,
                'template': result_data,
                'generation': generation_result
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            # 检查是否有关联的问题
            usage_count = Question.objects.filter(template_id=template_id).count()
            if usage_count > 0:
                return error(message=f'此模板已被 {usage_count} 个问题使用，无法删除', response_status=status.HTTP_400_BAD_REQUEST)
            
            template.delete()
            
            from rest_framework.response import Response
            return Response({
                'success': True,
                'message': '模板删除成功'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取问题详情',
    responses={200: openapi.Response('问题详情')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新问题',
    request_body=QuestionSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='patch',
    operation_summary='部分更新问题',
    request_body=QuestionSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除问题',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def question_detail_update_delete(request, project_id, question_id):
    """获取、更新或删除问题"""
    try:
        project = get_object_or_404(Project, id=project_id)
        question = get_object_or_404(Question, id=question_id, project=project)
    except Exception as e:
        return error(message='问题不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            serializer = QuestionSerializer(question)
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method in ['PUT', 'PATCH']:
        try:
            serializer = QuestionSerializer(question, data=request.data, partial=True)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            question.delete()
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='delete',
    operation_summary='批量删除问题',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'questionIds': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description='问题ID列表'
            )
        },
        required=['questionIds']
    ),
    responses={200: openapi.Response('删除成功')}
)
@api_view(['DELETE'])
def question_batch_delete(request, project_id):
    """批量删除问题"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    try:
        # 获取问题ID列表
        question_ids = request.data.get('questionIds', [])
        
        if not question_ids or not isinstance(question_ids, list) or len(question_ids) == 0:
            return error(message='问题ID列表不能为空', response_status=status.HTTP_400_BAD_REQUEST)
        
        # 验证所有问题都属于该项目
        questions = Question.objects.filter(id__in=question_ids, project=project)
        found_count = questions.count()
        
        if found_count == 0:
            return error(message='问题不存在', response_status=status.HTTP_404_NOT_FOUND)
        
        if found_count != len(question_ids):
            # 部分问题不存在或不属于该项目
            found_ids = set(questions.values_list('id', flat=True))
            missing_ids = [qid for qid in question_ids if qid not in found_ids]
            return error(
                message=f'部分问题不存在或不属于该项目: {missing_ids}',
                response_status=status.HTTP_400_BAD_REQUEST
            )
        
        # 批量删除问题（级联删除会处理关联的数据集）
        deleted_count = questions.delete()[0]
        
        return success(data={
            'success': True,
            'message': f'成功删除 {deleted_count} 个问题',
            'deletedCount': deleted_count
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary='获取问题树形视图数据',
    manual_parameters=[
        openapi.Parameter('tag', openapi.IN_QUERY, description='标签名', type=openapi.TYPE_STRING),
        openapi.Parameter('input', openapi.IN_QUERY, description='搜索关键词', type=openapi.TYPE_STRING),
        openapi.Parameter('tagsOnly', openapi.IN_QUERY, description='仅返回标签', type=openapi.TYPE_BOOLEAN),
        openapi.Parameter('isDistill', openapi.IN_QUERY, description='是否蒸馏问题', type=openapi.TYPE_BOOLEAN),
        openapi.Parameter('excludeImage', openapi.IN_QUERY, description='排除图片问题', type=openapi.TYPE_BOOLEAN),
    ],
    responses={200: openapi.Response('问题树形数据')}
)
@api_view(['GET'])
def question_tree(request, project_id):
    """获取问题树形视图数据"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    try:
        # 获取查询参数
        tag = request.GET.get('tag')
        input_text = request.GET.get('input')
        tags_only = request.GET.get('tagsOnly') == 'true'
        is_distill = request.GET.get('isDistill') == 'true'
        exclude_image = request.GET.get('excludeImage', 'true') != 'false'  # 默认排除图片问题
        
        # 构建基础查询
        queryset = Question.objects.filter(project=project)
        
        # 排除图片问题（label='image'）
        if exclude_image:
            queryset = queryset.exclude(label='image')
        
        # 如果是蒸馏问题，需要过滤蒸馏文本块
        if is_distill:
            distill_chunk = Chunk.objects.filter(
                project=project,
                name='Distilled Content'
            ).first()
            if distill_chunk:
                queryset = queryset.filter(chunk=distill_chunk)
        
        if tag:
            # 获取指定标签的问题数据（包含完整字段）
            # 搜索关键词过滤 - 与 Node.js 的 getQuestionsByTag 保持一致：只在 input 存在时添加过滤
            if input_text:
                queryset = queryset.filter(question__icontains=input_text)
            # 获取指定标签的问题数据（包含完整字段）
            # 处理未分类问题
            if tag == 'uncategorized':
                from tags.models import Tag
                # 获取所有标签的 label
                all_tags = Tag.objects.filter(project=project)
                
                def extract_all_labels(tag_obj):
                    labels = [tag_obj.label]
                    children = Tag.objects.filter(parent_id=tag_obj.id, project=project)
                    for child in children:
                        labels.extend(extract_all_labels(child))
                    return labels
                
                all_tag_labels = []
                for root_tag in all_tags.filter(parent_id__isnull=True):
                    all_tag_labels.extend(extract_all_labels(root_tag))
                
                # 查询不在任何标签中的问题
                from django.db.models import Q
                if exclude_image:
                    if all_tag_labels:
                        queryset = queryset.exclude(
                            Q(label__in=all_tag_labels) | Q(label='image')
                        )
                    else:
                        queryset = queryset.exclude(label='image')
                else:
                    if all_tag_labels:
                        queryset = queryset.exclude(label__in=all_tag_labels)
                    else:
                        queryset = queryset.filter(Q(label__isnull=True) | Q(label=''))
            elif exclude_image and tag == 'image':
                # 如果排除图片且标签是 image，返回空数组
                from rest_framework.response import Response
                return Response([], status=status.HTTP_200_OK)
            else:
                # 普通标签查询
                queryset = queryset.filter(label=tag)
            
            questions = queryset.order_by('-create_at')
            
            # 批量查询 datasetCount 和 conversationCount
            from datasets.models import Dataset
            from conversations.models import DatasetConversation
            from django.db.models import Count
            question_ids = list(questions.values_list('id', flat=True))
            dataset_counts = {}
            conversation_counts = {}
            if question_ids:
                d_counts = Dataset.objects.filter(question_id__in=question_ids).values('question_id').annotate(
                    count=Count('id')
                )
                dataset_counts = {item['question_id']: item['count'] for item in d_counts}
                
                c_counts = DatasetConversation.objects.filter(question_id__in=question_ids).values('question_id').annotate(
                    count=Count('id')
                )
                conversation_counts = {item['question_id']: item['count'] for item in c_counts}
            
            # 序列化问题数据并添加 datasetCount
            # 预加载 chunk 数据，避免 N+1 查询
            questions_with_chunks = questions.select_related('chunk')
            serializer = QuestionSerializer(questions_with_chunks, many=True)
            questions_data = []
            for idx, q_data in enumerate(serializer.data):
                question_obj = questions_with_chunks[idx]
                # 添加 dataset_count 字段（使用 snake_case，前端会兼容处理）
                q_data['dataset_count'] = dataset_counts.get(q_data['id'], 0)
                q_data['conversation_count'] = conversation_counts.get(q_data['id'], 0)
                # 添加 chunk 对象（如果存在），与 Node.js 的 include 格式一致
                if question_obj.chunk:
                    q_data['chunk'] = {
                        'name': question_obj.chunk.name,
                        'content': question_obj.chunk.content
                    }
                questions_data.append(q_data)
            
            # 与 Node.js 一致：直接返回数组，不使用 success() 包装
            from rest_framework.response import Response
            return Response(questions_data, status=status.HTTP_200_OK)
        elif tags_only:
            # 只获取标签信息（仅包含 id, label 和 answered 字段）
            # 与 Node.js 的 getQuestionsForTree 保持一致，返回 {id, label, answered}
            # 搜索关键词过滤 - 与 Node.js 保持一致：即使 input 为空，也添加过滤条件
            # 注意：在 Node.js 中，question: { contains: input || '' } 会匹配所有记录（空字符串包含在任何字符串中）
            # 在 Django 中，如果 input_text 为空字符串，icontains 也会匹配所有记录
            if input_text is not None:
                queryset = queryset.filter(question__icontains=input_text or '')
            
            questions = queryset.order_by('-create_at').values('id', 'label', 'answered')
            tree_data = [
                {
                    'id': q['id'],
                    'label': q['label'] or '',  # 空标签也返回
                    'answered': q['answered']
                }
                for q in questions
            ]
            # 与 Node.js 一致：直接返回数组
            from rest_framework.response import Response
            return Response(tree_data, status=status.HTTP_200_OK)
        else:
            # 兼容原有请求，获取树形视图数据（仅包含 id 和 label 字段）
            questions = queryset.order_by('-create_at').values('id', 'label', 'answered')
            tree_data = [
                {
                    'id': q['id'],
                    'label': q['label'],
                    'answered': q['answered']
                }
                for q in questions
            ]
            # 与 Node.js 一致：直接返回数组
            from rest_framework.response import Response
            return Response(tree_data, status=status.HTTP_200_OK)
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)