"""
问题模型（从 Prisma Schema 转换）
"""
from django.db import models
from django.utils import timezone
from nanoid import generate
from projects.models import Project
from chunks.models import Chunk


def generate_id():
    """生成ID（对应Prisma的nanoid()）"""
    return generate()


class Question(models.Model):
    """问题模型（对应 Prisma Questions）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='questions', db_column='projectId')
    chunk = models.ForeignKey(Chunk, on_delete=models.CASCADE, related_name='questions', db_column='chunkId')
    ga_pair_id = models.CharField(max_length=255, null=True, blank=True, db_column='gaPairId')
    question = models.TextField()
    label = models.CharField(max_length=255, default='')
    answered = models.BooleanField(default=False)
    image_id = models.CharField(max_length=255, null=True, blank=True, db_column='imageId')
    image_name = models.CharField(max_length=255, null=True, blank=True, db_column='imageName')
    template_id = models.CharField(max_length=255, null=True, blank=True, db_column='templateId')
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'questions'
        ordering = ['-create_at']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['image_id']),
            models.Index(fields=['template_id']),
        ]
        verbose_name = '问题'
        verbose_name_plural = '问题'
    
    def __str__(self):
        return self.question[:50] if len(self.question) > 50 else self.question


class QuestionTemplate(models.Model):
    """问题模板模型（对应 Prisma QuestionTemplates）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='question_templates', db_column='projectId')
    question = models.TextField()  # Question content
    source_type = models.CharField(max_length=50, db_column='sourceType')  # 'image' | 'text'
    answer_type = models.CharField(max_length=50, db_column='answerType')  # 'text' | 'label' | 'custom_format'
    description = models.TextField(default='')
    labels = models.TextField(default='')  # JSON array of label options
    custom_format = models.TextField(default='', db_column='customFormat')  # Custom format definition
    order = models.IntegerField(default=0)  # Display order
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'question_templates'
        ordering = ['order', '-create_at']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['project', 'source_type']),
        ]
        verbose_name = '问题模板'
        verbose_name_plural = '问题模板'
    
    def __str__(self):
        return self.question[:50] if len(self.question) > 50 else self.question
