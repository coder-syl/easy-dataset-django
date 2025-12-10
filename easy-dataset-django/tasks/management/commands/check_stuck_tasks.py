"""
检查并修复卡住的任务
使用方法: python manage.py check_stuck_tasks
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
import logging

logger = logging.getLogger('tasks')


class Command(BaseCommand):
    help = '检查并修复卡住的任务（超过2小时仍在处理中的任务）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅检查，不实际修复',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=2,
            help='超时时间（小时），默认2小时',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        timeout_hours = options['hours']
        
        self.stdout.write(f'检查超过 {timeout_hours} 小时仍在处理中的任务...')
        
        # 查找所有处理中的任务
        pending_tasks = Task.objects.filter(status=0)  # 0=处理中
        
        stuck_tasks = []
        for task in pending_tasks:
            is_stuck = False
            reason = None
            elapsed = None
            
            # 检查1: totalCount为0且创建时间超过1小时的任务（异常任务）
            if task.total_count == 0:
                if task.create_at:
                    elapsed = timezone.now() - task.create_at
                    if elapsed > timedelta(hours=1):
                        is_stuck = True
                        reason = f'totalCount为0的异常任务（创建时间: {elapsed}）'
                else:
                    is_stuck = True
                    reason = 'totalCount为0且无创建时间的异常任务'
            
            # 检查2: 超时任务（超过指定小时数）
            if not is_stuck and task.start_time:
                elapsed = timezone.now() - task.start_time
                if elapsed > timedelta(hours=timeout_hours):
                    is_stuck = True
                    reason = f'任务超时（运行时间: {elapsed}）'
            
            # 检查3: 没有开始时间的任务
            if not is_stuck and not task.start_time:
                if task.create_at:
                    elapsed = timezone.now() - task.create_at
                    if elapsed > timedelta(hours=1):
                        is_stuck = True
                        reason = f'没有开始时间的异常任务（创建时间: {elapsed}）'
                else:
                    is_stuck = True
                    reason = '没有开始时间和创建时间的异常任务'
            
            if is_stuck:
                stuck_tasks.append({
                    'task': task,
                    'elapsed': elapsed,
                    'reason': reason
                })
        
        if not stuck_tasks:
            self.stdout.write(self.style.SUCCESS('没有发现卡住的任务'))
            return
        
        self.stdout.write(self.style.WARNING(f'发现 {len(stuck_tasks)} 个卡住的任务:'))
        
        for item in stuck_tasks:
            task = item['task']
            elapsed = item['elapsed']
            reason = item['reason']
            elapsed_str = str(elapsed) if elapsed else '无时间信息'
            
            self.stdout.write(
                f'  - 任务ID: {task.id}, 类型: {task.task_type}, '
                f'totalCount: {task.total_count}, 创建时间: {task.create_at}, '
                f'原因: {reason}'
            )
            
            if not dry_run:
                # 标记为失败
                task.status = 2  # 失败
                task.detail = f'任务异常：{reason}（由系统自动检测）'
                task.end_time = timezone.now()
                task.save()
                self.stdout.write(self.style.SUCCESS(f'    已标记为失败'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n这是预览模式，未实际修改。使用 --no-dry-run 来实际修复。'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n已修复 {len(stuck_tasks)} 个卡住的任务'))

