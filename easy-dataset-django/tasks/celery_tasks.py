"""
Celery任务定义
"""
from celery import shared_task
from .models import Task
from .task_handlers import (
    process_question_generation_task,
    process_answer_generation_task,
    process_file_processing_task,
    process_data_cleaning_task,
    process_dataset_evaluation_task,
    process_multi_turn_generation_task,
    process_data_distillation_task,
    process_image_question_generation_task,
    process_image_dataset_generation_task,
    process_image_dataset_evaluation_task
)


@shared_task(bind=True, max_retries=3, name='tasks.celery_tasks.process_task_async')
def process_task_async(self, task_id):
    """
    异步处理任务
    :param task_id: 任务ID
    """
    import logging
    from django.utils import timezone
    from datetime import timedelta
    
    logger = logging.getLogger('tasks')
    
    try:
        task = Task.objects.get(id=task_id)
        
        # 如果任务已经完成或失败，不再处理
        if task.status in [1, 2]:  # 1=已完成, 2=失败
            logger.info(f'[Task {task_id}] 任务已完成或失败，跳过处理')
            return {'status': 'skipped', 'reason': 'Task already completed or failed'}
        
        # 检查任务是否超时（超过2小时）
        if task.start_time and (timezone.now() - task.start_time) > timedelta(hours=2):
            logger.warning(f'[Task {task_id}] 任务超时（超过2小时），标记为失败')
            task.status = 2  # 失败
            task.detail = f'任务超时：任务已运行超过2小时，可能已卡住或失败'
            task.end_time = timezone.now()
            task.save()
            return {'status': 'timeout', 'reason': 'Task timeout'}
        
        # 更新任务状态为处理中（如果还没有开始时间，设置开始时间）
        if not task.start_time:
            task.start_time = timezone.now()
        task.status = 0  # 0=处理中
        task.save()
        
        logger.info(f'[Task {task_id}] 开始处理任务: {task.task_type}')
        
        # 根据任务类型调用相应的处理函数
        task_type = task.task_type
        
        if task_type == 'question-generation':
            process_question_generation_task(task)
        elif task_type == 'answer-generation':
            process_answer_generation_task(task)
        elif task_type == 'file-processing':
            process_file_processing_task(task)
        elif task_type == 'data-cleaning':
            process_data_cleaning_task(task)
        elif task_type == 'dataset-evaluation':
            process_dataset_evaluation_task(task)
        elif task_type == 'multi-turn-generation':
            process_multi_turn_generation_task(task)
        elif task_type == 'data-distillation':
            process_data_distillation_task(task)
        elif task_type == 'image-question-generation':
            process_image_question_generation_task(task)
        elif task_type == 'image-dataset-generation':
            process_image_dataset_generation_task(task)
        elif task_type == 'image-dataset-evaluation':
            process_image_dataset_evaluation_task(task)
        else:
            task.status = 2  # 失败
            task.note = f'未知任务类型: {task_type}'
            task.end_time = timezone.now()
            task.save()
            logger.error(f'[Task {task_id}] 未知任务类型: {task_type}')
            return {'status': 'failed', 'reason': f'Unknown task type: {task_type}'}
        
        logger.info(f'[Task {task_id}] 任务处理完成')
        return {'status': 'completed', 'task_id': task_id}
    except Task.DoesNotExist:
        logger.error(f'[Task {task_id}] 任务不存在')
        return {'status': 'failed', 'reason': f'Task not found: {task_id}'}
    except Exception as e:
        # 更新任务状态为失败
        logger.error(f'[Task {task_id}] 任务处理异常: {str(e)}', exc_info=True)
        try:
            task = Task.objects.get(id=task_id)
            task.status = 2  # 失败
            task.detail = f'处理失败: {str(e)}'
            task.end_time = timezone.now()
            task.save()
        except:
            pass
        
        # 重试（最多3次）
        if self.request.retries < self.max_retries:
            logger.warning(f'[Task {task_id}] 任务处理失败，将重试 ({self.request.retries + 1}/{self.max_retries})')
            raise self.retry(exc=e, countdown=60)
        else:
            logger.error(f'[Task {task_id}] 任务处理失败，已达到最大重试次数')
            return {'status': 'failed', 'reason': str(e)}


@shared_task
def recover_pending_tasks():
    """
    恢复待处理的任务
    查找所有处理中的任务并检查超时
    """
    import logging
    from django.utils import timezone
    from datetime import timedelta
    
    logger = logging.getLogger('tasks')
    
    pending_tasks = Task.objects.filter(status=0)  # 0=处理中
    recovered_count = 0
    timeout_count = 0
    
    for task in pending_tasks:
        # 检查1: totalCount为0且创建时间超过1小时的任务（异常任务）
        if task.total_count == 0:
            if task.create_at:
                elapsed = timezone.now() - task.create_at
                if elapsed > timedelta(hours=1):
                    logger.warning(f'[Task {task.id}] totalCount为0的异常任务（创建时间: {elapsed}），标记为失败')
                    task.status = 2  # 失败
                    task.detail = f'任务异常：totalCount为0，可能是创建时文件列表为空（由系统自动检测）'
                    task.end_time = timezone.now()
                    task.save()
                    timeout_count += 1
                    continue
            else:
                logger.warning(f'[Task {task.id}] totalCount为0且无创建时间的异常任务，标记为失败')
                task.status = 2  # 失败
                task.detail = '任务异常：totalCount为0且无创建时间'
                task.end_time = timezone.now()
                task.save()
                timeout_count += 1
                continue
        
        # 检查2: 任务是否超时（超过2小时）
        if task.start_time:
            elapsed = timezone.now() - task.start_time
            if elapsed > timedelta(hours=2):
                # 任务超时，标记为失败
                logger.warning(f'[Task {task.id}] 任务超时（运行时间: {elapsed}），标记为失败')
                task.status = 2  # 失败
                task.detail = f'任务超时：任务已运行 {elapsed}，可能已卡住或失败'
                task.end_time = timezone.now()
                task.save()
                timeout_count += 1
            elif elapsed > timedelta(hours=1):
                # 任务运行超过1小时但未超过2小时，尝试重新处理
                logger.info(f'[Task {task.id}] 任务运行超过1小时，尝试重新处理')
                process_task_async.delay(task.id)
                recovered_count += 1
        else:
            # 没有开始时间，检查创建时间
            if task.create_at:
                elapsed = timezone.now() - task.create_at
                if elapsed > timedelta(hours=1):
                    logger.warning(f'[Task {task.id}] 任务没有开始时间且创建时间超过1小时（{elapsed}），标记为失败')
                    task.status = 2  # 失败
                    task.detail = f'任务异常：没有开始时间（创建时间: {elapsed}）'
                    task.end_time = timezone.now()
                    task.save()
                    timeout_count += 1
            else:
                # 没有开始时间和创建时间，可能是异常任务，标记为失败
                logger.warning(f'[Task {task.id}] 任务没有开始时间和创建时间，可能是异常任务，标记为失败')
                task.status = 2  # 失败
                task.detail = '任务异常：没有开始时间和创建时间'
                task.end_time = timezone.now()
                task.save()
                timeout_count += 1
    
    logger.info(f'任务恢复检查完成: 恢复={recovered_count}, 超时标记失败={timeout_count}, 总数={pending_tasks.count()}')
    return {
        'recovered': recovered_count,
        'timeout': timeout_count,
        'total': pending_tasks.count()
    }

