"""
标签模型（对应 Prisma Tags）
"""
from django.db import models
from nanoid import generate
from projects.models import Project


def generate_id():
    """生成ID（对应Prisma的nanoid()）"""
    return generate()


class Tag(models.Model):
    """标签模型（对应 Prisma Tags）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    label = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tags', db_column='projectId')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', db_column='parentId')

    class Meta:
        db_table = 'tags'
        ordering = ['label']
        verbose_name = '标签'
        verbose_name_plural = '标签'

    def __str__(self):
        return self.label
