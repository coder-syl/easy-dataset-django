"""
启动Celery Beat的管理命令
用法: python manage.py start_celery_beat
"""
from django.core.management.base import BaseCommand
import subprocess


class Command(BaseCommand):
    help = '启动Celery Beat (定时任务调度器)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('启动Celery Beat'))
        
        # 启动Celery Beat
        cmd = [
            'celery',
            '-A', 'easy_dataset',
            'beat',
            '--loglevel', 'info'
        ]
        
        try:
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nCelery Beat已停止'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'启动Celery Beat失败: {e}'))

