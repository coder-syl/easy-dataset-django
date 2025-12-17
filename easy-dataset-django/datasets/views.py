"""
数据集管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
import json

from projects.models import Project
from .models import Dataset
from .serializers import DatasetSerializer, DatasetCreateSerializer
from common.response.result import success, error


@swagger_auto_schema(
    method='get',
    operation_summary='获取数据集列表',
    responses={200: openapi.Response('数据集列表')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='生成数据集',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'questionId': openapi.Schema(type=openapi.TYPE_STRING),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('生成成功')}
)
@api_view(['GET', 'POST'])
def dataset_list_create(request, project_id):
    """获取数据集列表或生成数据集"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            # 获取查询参数
            page = int(request.GET.get('page', 1))
            size = int(request.GET.get('size', 10))
            input_text = request.GET.get('input', '')
            field = request.GET.get('field', 'question')
            status_param = request.GET.get('status')
            has_cot = request.GET.get('hasCot', 'all')
            is_distill = request.GET.get('isDistill', 'all')
            score_range = request.GET.get('scoreRange', '')
            custom_tag = request.GET.get('customTag', '')
            note_keyword = request.GET.get('noteKeyword', '')
            chunk_name = request.GET.get('chunkName', '')
            get_all_ids = request.GET.get('getAllIds') == 'true'
            
            # 构建查询
            queryset = Dataset.objects.filter(project=project)
            
            # 搜索条件
            if input_text:
                if field == 'question':
                    queryset = queryset.filter(question__icontains=input_text)
                elif field == 'answer':
                    queryset = queryset.filter(answer__icontains=input_text)
                elif field == 'cot':
                    queryset = queryset.filter(cot__icontains=input_text)
                elif field == 'questionLabel':
                    queryset = queryset.filter(question_label__icontains=input_text)
            
            # 确认状态筛选
            if status_param == 'confirmed':
                queryset = queryset.filter(confirmed=True)
            elif status_param == 'unconfirmed':
                queryset = queryset.filter(confirmed=False)
            
            # 思维链筛选
            if has_cot == 'yes':
                queryset = queryset.exclude(cot='')
            elif has_cot == 'no':
                queryset = queryset.filter(cot='')
            
            # 蒸馏数据集筛选
            if is_distill == 'yes':
                queryset = queryset.filter(chunk_name='Distilled Content')
            elif is_distill == 'no':
                queryset = queryset.exclude(chunk_name='Distilled Content')
            
            # 评分范围筛选
            if score_range:
                try:
                    min_score, max_score = map(float, score_range.split('-'))
                    queryset = queryset.filter(score__gte=min_score, score__lte=max_score)
                except:
                    pass
            
            # 标签筛选
            if custom_tag:
                queryset = queryset.filter(tags__icontains=custom_tag)
            
            # 备注关键词筛选
            if note_keyword:
                queryset = queryset.filter(note__icontains=note_keyword)
            
            # 文本块名称筛选
            if chunk_name:
                queryset = queryset.filter(chunk_name__icontains=chunk_name)
            
            # 如果只需要ID列表（支持 selectedAll 参数，与 Node.js 对齐）
            selected_all = request.GET.get('selectedAll') == 'true'
            if get_all_ids or selected_all:
                dataset_ids = queryset.values_list('id', flat=True)
                return success(data=[{'id': str(id)} for id in dataset_ids])
            
            # 分页
            paginator = Paginator(queryset.order_by('-create_at'), size)
            page_obj = paginator.get_page(page)
            
            # 计算确认的数据集数量（与 Node.js 对齐）
            confirmed_queryset = queryset.filter(confirmed=True)
            confirmed_count = confirmed_queryset.count()
            
            serializer = DatasetSerializer(page_obj.object_list, many=True)
            return success(data={
                'data': serializer.data,
                'total': paginator.count,
                'confirmedCount': confirmed_count
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            # 生成数据集（暂时返回占位响应，后续需要集成LLM调用逻辑）
            question_id = request.data.get('questionId')
            model = request.data.get('model')
            language = request.data.get('language', 'zh-CN')
            
            if not question_id or not model:
                return error(message='问题ID和模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 集成数据集生成逻辑
            from .services import generate_dataset_for_question
            
            try:
                dataset = generate_dataset_for_question(project_id, question_id, {
                    'model': model,
                    'language': language
                })
                
                return success(data=dataset)
            except Exception as e:
                return error(message=f'生成数据集失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='评估单个数据集',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('评估结果')}
)
@api_view(['POST'])
def dataset_evaluate(request, project_id, dataset_id):
    """评估单个数据集"""
    from .services import evaluate_dataset_service
    
    model = request.data.get('model')
    language = request.data.get('language', 'zh-CN')
    
    if not model:
        return error(message='Model cannot be empty', response_status=status.HTTP_400_BAD_REQUEST)
    
    result = evaluate_dataset_service(project_id, dataset_id, model, language)
    
    if not result.get('success'):
        return error(
            message=result.get('error', '评估失败'),
            response_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # 返回格式与Node.js版本一致：{success: true, message: '...', data: {...}}
    from django.http import JsonResponse
    return JsonResponse({
        'success': True,
        'message': '数据集评估完成',
        'data': {
            'score': result.get('score'),
            'aiEvaluation': result.get('evaluation')
        }
    })


@swagger_auto_schema(
    method='post',
    operation_summary='批量评估数据集',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'language': openapi.Schema(type=openapi.TYPE_STRING),
            'datasetIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
        }
    ),
    responses={200: openapi.Response('批量评估结果')}
)
@api_view(['POST'])
def dataset_batch_evaluate(request, project_id):
    """批量评估数据集"""
    from tasks.models import Task
    import json
    
    model = request.data.get('model')
    language = request.data.get('language', 'zh-CN')
    
    if not model or not model.get('modelName'):
        return error(message='模型配置不能为空', response_status=status.HTTP_400_BAD_REQUEST)
    
    # 创建批量评估任务
    try:
        project = get_object_or_404(Project, id=project_id)
        task = Task.objects.create(
            project=project,
            task_type='dataset-evaluation',
            status=0,
            model_info=json.dumps(model),
            language=language,
            detail='',
            total_count=0,
            note='准备开始批量评估数据集质量...',
            completed_count=0
        )
        
        # 异步处理任务
        from tasks.celery_tasks import process_task_async
        process_task_async.delay(task.id)
        
        # 返回格式与Node.js版本一致：{success: true, message: '...', data: {...}}
        from django.http import JsonResponse
        return JsonResponse({
            'success': True,
            'message': '批量评估任务已创建',
            'data': {'taskId': task.id}
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary='优化数据集',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'datasetId': openapi.Schema(type=openapi.TYPE_STRING),
            'model': openapi.Schema(type=openapi.TYPE_OBJECT),
            'advice': openapi.Schema(type=openapi.TYPE_STRING),
            'language': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={200: openapi.Response('优化结果')}
)
@api_view(['POST'])
def dataset_optimize(request, project_id):
    """优化数据集（与 Node.js 版本对齐）"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)

    dataset_id = request.data.get('datasetId')
    model = request.data.get('model')
    advice = request.data.get('advice')
    language = request.data.get('language', 'zh-CN')
    
    if not dataset_id:
        return error(message='datasetId 不能为空', response_status=status.HTTP_400_BAD_REQUEST)
    
    if not model:
        return error(message='Model cannot be empty', response_status=status.HTTP_400_BAD_REQUEST)
    
    if not advice:
        return error(message='Please provide optimization suggestions', response_status=status.HTTP_400_BAD_REQUEST)

    try:
        dataset = get_object_or_404(Dataset, id=dataset_id, project=project)
        
        # 获取原始文本块内容
        chunk_content = dataset.chunk_content or ''
        
        # 如果数据集中没有chunk_content，尝试通过question_id查找
        if not chunk_content and dataset.question_id:
            try:
                from questions.models import Question
                from chunks.models import Chunk
                question = Question.objects.filter(
                    id=dataset.question_id,
                    project_id=project_id
                ).first()
                
                if question and question.chunk_id:
                    chunk = Chunk.objects.filter(id=question.chunk_id).first()
                    if chunk:
                        chunk_content = chunk.content or ''
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'无法获取原始文本块内容: {str(e)}')
        
        # 调用优化服务
        from .services import optimize_dataset_service
        result = optimize_dataset_service(
            project_id,
            dataset_id,
            dataset.question,
            dataset.answer,
            dataset.cot or '',
            advice,
            chunk_content,
            model,
            language
        )
        
        if not result.get('success'):
            return error(
                message=result.get('error', '优化失败'),
                response_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # 返回格式与 Node.js 一致
        from django.http import JsonResponse
        return JsonResponse({
            'success': True,
            'dataset': result.get('dataset')
        })
    except Exception as e:
        return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='get',
    operation_summary='获取数据集详情',
    responses={200: openapi.Response('数据集详情')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='更新数据集',
    request_body=DatasetSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='patch',
    operation_summary='部分更新数据集',
    request_body=DatasetSerializer,
    responses={200: openapi.Response('更新成功')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除数据集',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def dataset_detail_update_delete(request, project_id, dataset_id):
    """获取、更新或删除数据集"""
    import logging
    logger = logging.getLogger('datasets')
    
    # 验证项目是否存在
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.warning(f'项目不存在: {project_id}')
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'查询项目时发生错误: {str(e)}', exc_info=True)
        return error(message=f'查询项目失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 验证数据集是否存在
    try:
        dataset = Dataset.objects.get(id=dataset_id, project=project)
        logger.info(f'找到数据集: {dataset_id}, 项目: {project_id}')
    except Dataset.DoesNotExist:
        # 检查数据集是否存在（可能项目不匹配）
        dataset_exists = Dataset.objects.filter(id=dataset_id).exists()
        if dataset_exists:
            logger.warning(f'数据集 {dataset_id} 存在，但不属于项目 {project_id}')
            return error(message=f'数据集 {dataset_id} 不属于当前项目', response_status=status.HTTP_404_NOT_FOUND)
        else:
            logger.warning(f'数据集不存在: {dataset_id}, 项目: {project_id}')
            # 列出项目中的所有数据集ID，用于调试
            all_dataset_ids = list(Dataset.objects.filter(project=project).values_list('id', flat=True)[:10])
            logger.info(f'项目 {project_id} 中的数据集ID示例: {all_dataset_ids}')
            return error(message='数据集不存在', response_status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'查询数据集时发生错误: {str(e)}', exc_info=True)
        return error(message=f'查询数据集失败: {str(e)}', response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if request.method == 'GET':
        try:
            # 检查是否是导航操作（获取上一个/下一个数据集）
            operate_type = request.GET.get('operateType')
            if operate_type:
                from django.db.models import Q
                current_create_at = dataset.create_at
                
                if operate_type == 'prev':
                    # 获取上一个数据集（创建时间更早的）
                    nav_dataset = Dataset.objects.filter(
                        project=project,
                        create_at__lt=current_create_at
                    ).order_by('-create_at').first()
                elif operate_type == 'next':
                    # 获取下一个数据集（创建时间更晚的）
                    nav_dataset = Dataset.objects.filter(
                        project=project,
                        create_at__gt=current_create_at
                    ).order_by('create_at').first()
                else:
                    nav_dataset = None
                
                if nav_dataset:
                    serializer = DatasetSerializer(nav_dataset)
                    return success(data=serializer.data)
                else:
                    return success(data=None)
            
            # 普通获取详情，返回数据集信息和统计
            serializer = DatasetSerializer(dataset)
            
            # 获取数据集统计信息（与 Node.js 对齐）
            from django.db.models import Count, Q
            total_count = Dataset.objects.filter(project=project).count()
            confirmed_count = Dataset.objects.filter(project=project, confirmed=True).count()
            
            return success(data={
                'datasets': serializer.data,
                'datasetsAllCount': total_count,
                'datasetsConfirmCount': confirmed_count
            })
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            serializer = DatasetSerializer(dataset, data=request.data, partial=True)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PATCH':
        try:
            # 处理 tags 字段：如果是数组，转换为 JSON 字符串
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            if 'tags' in data and isinstance(data['tags'], list):
                data['tags'] = json.dumps(data['tags'], ensure_ascii=False)
            elif 'tags' in data and isinstance(data['tags'], dict):
                data['tags'] = json.dumps(data['tags'], ensure_ascii=False)
            
            serializer = DatasetSerializer(dataset, data=data, partial=True)
            if not serializer.is_valid():
                return error(message=serializer.errors, response_status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return success(data=serializer.data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            # 保存 question_id 用于后续检查
            question_id = dataset.question_id
            
            # 删除数据集
            dataset.delete()
            
            # 检查该问题是否还有其他数据集（与 Node.js 对齐）
            from .models import Dataset
            remaining_count = Dataset.objects.filter(question_id=question_id).count()
            
            # 如果没有其他数据集，将问题的 answered 状态改为 false
            if remaining_count == 0:
                from questions.models import Question
                try:
                    question = Question.objects.get(id=question_id)
                    question.answered = False
                    question.save()
                except Question.DoesNotExist:
                    pass  # 问题不存在，忽略
            
            return success(data={'success': True})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
