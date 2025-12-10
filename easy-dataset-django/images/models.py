"""
图像模型（从 Prisma Schema 转换）
"""
from django.db import models
from django.utils import timezone
from nanoid import generate
from projects.models import Project


def generate_id():
    """生成ID（对应Prisma的nanoid()）"""
    return generate()


class Image(models.Model):
    """图像模型（对应 Prisma Images）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images', db_column='projectId')
    image_name = models.CharField(max_length=255, db_column='imageName')
    path = models.CharField(max_length=500)  # 图片存储路径
    size = models.IntegerField()  # 文件大小（字节）
    width = models.IntegerField(null=True, blank=True)  # 图片宽度
    height = models.IntegerField(null=True, blank=True)  # 图片高度
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'images'
        ordering = ['-create_at']
        unique_together = [['project', 'image_name']]
        indexes = [
            models.Index(fields=['project']),
        ]
        verbose_name = '图像'
        verbose_name_plural = '图像'
    
    def __str__(self):
        return self.image_name


class ImageDataset(models.Model):
    """图像数据集模型（对应 Prisma ImageDatasets）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='image_datasets', db_column='projectId')
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='image_datasets', db_column='imageId')
    image_name = models.CharField(max_length=255, db_column='imageName')
    question_id = models.CharField(max_length=255, null=True, blank=True, db_column='questionId')
    question = models.TextField()
    answer = models.TextField()  # 存储所有答案类型：text, JSON数组（标签）, 或自定义格式JSON
    answer_type = models.CharField(max_length=50, default='text', db_column='answerType')  # 'text' | 'label' | 'custom_format'
    model = models.CharField(max_length=255)
    confirmed = models.BooleanField(default=False)
    score = models.FloatField(default=0.0)
    tags = models.CharField(max_length=500, default='')
    note = models.TextField(default='')
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'image_datasets'
        ordering = ['-create_at']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['image']),
            models.Index(fields=['question_id']),
        ]
        verbose_name = '图像数据集'
        verbose_name_plural = '图像数据集'
    
    def __str__(self):
        return f"{self.image_name} - {self.question[:30]}..."
