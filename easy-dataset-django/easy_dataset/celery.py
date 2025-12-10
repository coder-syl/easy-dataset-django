"""
Celery配置
"""
import os
import logging
from celery import Celery

logger = logging.getLogger('celery')

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'easy_dataset.settings')

app = Celery('easy_dataset')

# 从Django设置中加载配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务 - 使用字符串列表指定要发现的包
app.autodiscover_tasks(['tasks'])

@app.task(bind=True)
def debug_task(self):
    logger.debug(f'调试任务请求: {self.request!r}')

