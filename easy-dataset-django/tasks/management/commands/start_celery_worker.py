"""
启动Celery Worker的管理命令
用法: python manage.py start_celery_worker
"""
from django.core.management.base import BaseCommand
import subprocess
import sys


class Command(BaseCommand):
    help = '启动Celery Worker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loglevel',
            type=str,
            default='info',
            help='日志级别 (debug, info, warning, error, critical)'
        )
        parser.add_argument(
            '--concurrency',
            type=int,
            default=4,
            help='并发worker数量'
        )

    def handle(self, *args, **options):
        import os
        from django.conf import settings
        
        loglevel = options['loglevel']
        concurrency = options['concurrency']
        
        self.stdout.write(self.style.SUCCESS(f'启动Celery Worker (并发数: {concurrency}, 日志级别: {loglevel})'))
        
        # 确保在项目根目录下运行
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        # 启动Celery Worker
        cmd = [
            sys.executable,  # 使用当前Python解释器
            '-m', 'celery',
            '-A', 'easy_dataset',
            'worker',
            '--loglevel', loglevel,
            '--concurrency', str(concurrency),
            '--pool', 'solo' if sys.platform == 'win32' else 'prefork',
            '--without-gossip',  # 禁用gossip协议（Windows上可能有问题）
            '--without-mingle',  # 禁用mingle（Windows上可能有问题）
            '--without-heartbeat'  # 禁用heartbeat（Windows上可能有问题）
        ]
        
        self.stdout.write(self.style.WARNING(f'工作目录: {project_root}'))
        self.stdout.write(self.style.WARNING(f'执行命令: {" ".join(cmd)}'))
        
        try:
            subprocess.run(cmd, check=True, cwd=project_root)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nCelery Worker已停止'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'启动Celery Worker失败: {e}'))
            self.stdout.write(self.style.ERROR('请确保：'))
            self.stdout.write(self.style.ERROR('1. 如果使用Redis: Redis服务正在运行'))
            self.stdout.write(self.style.ERROR('   如果使用SQLite: 已安装sqlalchemy (默认配置，无需额外操作)'))
            self.stdout.write(self.style.ERROR('2. 在easy-dataset-django目录下运行此命令'))
            self.stdout.write(self.style.ERROR('3. 已安装所有依赖: pip install -r requirements.txt'))
            self.stdout.write(self.style.WARNING('\n提示:'))
            self.stdout.write(self.style.WARNING('  - 默认使用SQLite作为broker（无需安装Redis）'))
            self.stdout.write(self.style.WARNING('  - 如需使用Redis: python manage.py start_redis'))
            self.stdout.write(self.style.WARNING('  - 或设置环境变量: export CELERY_BROKER_URL=redis://localhost:6379/0'))
            self.stdout.write(self.style.WARNING('\n提示: 可以通过环境变量配置其他broker:'))
            self.stdout.write(self.style.WARNING('  - RabbitMQ: export CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//'))
            self.stdout.write(self.style.WARNING('  - SQLite: export CELERY_BROKER_URL=sqla+sqlite:///celery_broker.db'))
            self.stdout.write(self.style.WARNING('  - PostgreSQL: export CELERY_BROKER_URL=sqla+postgresql://user:pass@localhost/dbname'))

