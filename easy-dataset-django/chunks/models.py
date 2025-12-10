"""
文本块模型（从 Prisma Schema 转换）
"""
from django.db import models
from django.utils import timezone
from nanoid import generate
from projects.models import Project


def generate_id():
    """生成ID（对应Prisma的nanoid()）"""
    return generate()


class Chunk(models.Model):
    """文本块模型（对应 Prisma Chunks）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='chunks', db_column='projectId')
    file_id = models.CharField(max_length=255, db_column='fileId')
    file_name = models.CharField(max_length=255, db_column='fileName')
    content = models.TextField()
    summary = models.TextField(default='')
    size = models.IntegerField()
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'chunks'
        ordering = ['-create_at']
        indexes = [
            models.Index(fields=['project']),
        ]
        verbose_name = '文本块'
        verbose_name_plural = '文本块'
    
    def __str__(self):
        return self.name
