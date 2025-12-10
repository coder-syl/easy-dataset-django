"""
多轮对话模型（从 Prisma Schema 转换）
"""
from django.db import models
from django.utils import timezone
from nanoid import generate
from projects.models import Project


def generate_id():
    """生成ID（对应Prisma的nanoid()）"""
    return generate()


class DatasetConversation(models.Model):
    """多轮对话数据集模型（对应 Prisma DatasetConversations）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='dataset_conversations', db_column='projectId')
    question_id = models.CharField(max_length=255, db_column='questionId')  # 第一个问题Id
    question = models.TextField()  # 第一个问题
    chunk_id = models.CharField(max_length=255, db_column='chunkId')
    model = models.CharField(max_length=255)
    question_label = models.CharField(max_length=255, db_column='questionLabel')
    score = models.FloatField(default=0.0)
    ai_evaluation = models.TextField(default='', db_column='aiEvaluation')
    tags = models.CharField(max_length=500, default='')
    note = models.TextField(default='')
    scenario = models.CharField(max_length=255)  # 对话场景
    role_a = models.CharField(max_length=255, db_column='roleA')  # 角色A设定
    role_b = models.CharField(max_length=255, db_column='roleB')  # 角色B设定
    turn_count = models.IntegerField(db_column='turnCount')  # 实际轮数
    max_turns = models.IntegerField(db_column='maxTurns')  # 设置的最大轮数
    raw_messages = models.TextField(db_column='rawMessages')  # JSON存储完整对话
    confirmed = models.BooleanField(default=False)
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'dataset_conversations'
        ordering = ['-create_at']
        indexes = [
            models.Index(fields=['project']),
        ]
        verbose_name = '多轮对话数据集'
        verbose_name_plural = '多轮对话数据集'
    
    def __str__(self):
        return f"{self.question[:30]}..." if len(self.question) > 30 else self.question
