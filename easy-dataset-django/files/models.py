"""
文件模型（从 Prisma Schema 转换）
"""
from django.db import models
from django.utils import timezone
from nanoid import generate
from projects.models import Project


def generate_id():
    """生成ID（对应Prisma的nanoid()）"""
    return generate()


class UploadFile(models.Model):
    """上传文件模型（对应 Prisma UploadFiles）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='upload_files', db_column='projectId')
    file_name = models.CharField(max_length=255, db_column='fileName')
    file_ext = models.CharField(max_length=50, db_column='fileExt')
    path = models.CharField(max_length=500)
    size = models.IntegerField()
    md5 = models.CharField(max_length=32)
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'upload_files'
        ordering = ['-create_at']
        verbose_name = '上传文件'
        verbose_name_plural = '上传文件'
    
    def __str__(self):
        return self.file_name


class GaPair(models.Model):
    """GA对模型（对应 Prisma GaPairs）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='ga_pairs', db_column='projectId')
    upload_file = models.ForeignKey(UploadFile, on_delete=models.CASCADE, related_name='ga_pairs', db_column='fileId')
    pair_number = models.IntegerField(db_column='pairNumber')  # 1-5
    genre_title = models.CharField(max_length=255, db_column='genreTitle')  # Genre name/title
    genre_desc = models.TextField(db_column='genreDesc')  # Genre description
    audience_title = models.CharField(max_length=255, db_column='audienceTitle')  # Audience name/title
    audience_desc = models.TextField(db_column='audienceDesc')  # Audience description
    is_active = models.BooleanField(default=True, db_column='isActive')
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'ga_pairs'
        ordering = ['pair_number']
        unique_together = [['upload_file', 'pair_number']]
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['upload_file']),
        ]
        verbose_name = 'GA对'
        verbose_name_plural = 'GA对'
    
    def __str__(self):
        return f"{self.genre_title} - {self.audience_title}"
