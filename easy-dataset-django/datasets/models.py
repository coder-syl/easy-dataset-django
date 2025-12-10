"""
数据集模型（从 Prisma Schema 转换）
"""
from django.db import models
from django.utils import timezone
from nanoid import generate
from projects.models import Project


def generate_id():
    """生成ID（对应Prisma的nanoid()）"""
    return generate()


class Dataset(models.Model):
    """数据集模型（对应 Prisma Datasets）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='datasets', db_column='projectId')
    question_id = models.CharField(max_length=255, db_column='questionId')
    question = models.TextField()
    answer = models.TextField()
    answer_type = models.CharField(max_length=50, default='text', db_column='answerType')  # 'text' | 'label' | 'custom_format'
    chunk_name = models.CharField(max_length=255, db_column='chunkName')
    chunk_content = models.TextField(db_column='chunkContent')
    model = models.CharField(max_length=255)
    question_label = models.CharField(max_length=255, db_column='questionLabel')
    cot = models.TextField(default='')
    confirmed = models.BooleanField(default=False)
    score = models.FloatField(default=0.0)
    ai_evaluation = models.TextField(default='', db_column='aiEvaluation')
    tags = models.CharField(max_length=500, default='')
    note = models.TextField(default='')
    other = models.TextField(default='')  # JSON字符串
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'datasets'
        ordering = ['-create_at']
        indexes = [
            models.Index(fields=['project']),
        ]
        verbose_name = '数据集'
        verbose_name_plural = '数据集'
    
    def __str__(self):
        return f"{self.question[:30]}..." if len(self.question) > 30 else self.question
