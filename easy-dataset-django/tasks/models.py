"""
任务模型（从 Prisma Schema 转换）
"""
from django.db import models
from django.utils import timezone
from nanoid import generate
from projects.models import Project


def generate_id():
    """生成ID（对应Prisma的nanoid()）"""
    return generate()


class Task(models.Model):
    """任务模型（对应 Prisma Task）"""
    TASK_TYPE_CHOICES = [
        ('question-generation', '问题生成'),
        ('answer-generation', '答案生成'),
        ('file-processing', '文件处理'),
        ('data-cleaning', '数据清洗'),
        ('dataset-evaluation', '数据集评估'),
        ('multi-turn-generation', '多轮对话生成'),
        ('data-distillation', '数据蒸馏'),
        ('image-question-generation', '图像问题生成'),
        ('image-dataset-generation', '图像数据集生成'),
    ]
    
    STATUS_CHOICES = [
        (0, '处理中'),
        (1, '已完成'),
        (2, '失败'),
        (3, '已中断'),
    ]
    
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', db_column='projectId')
    task_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES, db_column='taskType')
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    start_time = models.DateTimeField(default=timezone.now, db_column='startTime')
    end_time = models.DateTimeField(null=True, blank=True, db_column='endTime')
    completed_count = models.IntegerField(default=0, db_column='completedCount')
    total_count = models.IntegerField(default=0, db_column='totalCount')
    model_info = models.TextField(db_column='modelInfo')  # JSON格式
    language = models.CharField(max_length=10, default='zh-CN')
    detail = models.TextField(default='')
    note = models.TextField(default='')
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'task'
        ordering = ['-create_at']
        indexes = [
            models.Index(fields=['project']),
        ]
        verbose_name = '任务'
        verbose_name_plural = '任务'
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.get_status_display()}"
