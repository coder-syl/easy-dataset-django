"""
项目模型（从 Prisma Schema 转换）
"""
from django.db import models
from django.utils import timezone
from nanoid import generate


def generate_id():
    """生成12位ID（对应Prisma的nanoid(12)）"""
    return generate(size=12)


class Project(models.Model):
    """项目模型（对应 Prisma Projects）"""
    id = models.CharField(max_length=12, primary_key=True, default=generate_id, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    global_prompt = models.TextField(default='')
    question_prompt = models.TextField(default='')
    answer_prompt = models.TextField(default='')
    label_prompt = models.TextField(default='')
    domain_tree_prompt = models.TextField(default='')
    clean_prompt = models.TextField(default='')
    default_model_config_id = models.CharField(max_length=255, null=True, blank=True)
    test = models.TextField(default='')
    create_at = models.DateTimeField(default=timezone.now)
    update_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        ordering = ['-create_at']
        verbose_name = '项目'
        verbose_name_plural = '项目'
    
    def __str__(self):
        return self.name
