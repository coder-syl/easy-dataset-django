from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tasks"
    
    def ready(self):
        """应用就绪时导入任务模块，确保Celery能发现任务"""
        try:
            # 显式导入任务模块，确保任务被注册
            import tasks.celery_tasks  # noqa: F401
        except ImportError:
            pass