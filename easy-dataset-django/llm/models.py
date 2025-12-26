"""
LLM模型（从 Prisma Schema 转换）
"""
from django.db import models
from django.utils import timezone
from nanoid import generate
from projects.models import Project


def generate_id():
    """生成ID（对应Prisma的nanoid()）"""
    return generate()


class LlmProvider(models.Model):
    """LLM提供商模型（对应 Prisma LlmProviders）"""
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    api_url = models.CharField(max_length=500, db_column='apiUrl')
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'llm_providers'
        ordering = ['name']
        verbose_name = 'LLM提供商'
        verbose_name_plural = 'LLM提供商'
    
    def __str__(self):
        return self.name


class LlmModel(models.Model):
    """LLM模型（对应 Prisma LlmModels）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    model_id = models.CharField(max_length=255, db_column='modelId')
    model_name = models.CharField(max_length=255, db_column='modelName')
    provider = models.ForeignKey(LlmProvider, on_delete=models.CASCADE, related_name='llm_models', db_column='providerId')
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'llm_models'
        ordering = ['model_name']
        verbose_name = 'LLM模型'
        verbose_name_plural = 'LLM模型'
    
    def __str__(self):
        return self.model_name


class ModelConfig(models.Model):
    """模型配置（对应 Prisma ModelConfig）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    provider_id = models.CharField(max_length=255, db_column='providerId')
    provider_name = models.CharField(max_length=255, db_column='providerName')
    endpoint = models.CharField(max_length=500)
    api_key = models.CharField(max_length=500, db_column='apiKey')
    model_id = models.CharField(max_length=255, db_column='modelId')
    model_name = models.CharField(max_length=255, db_column='modelName')
    type = models.CharField(max_length=50)  # 'text' | 'vision' | etc.
    temperature = models.FloatField()
    max_tokens = models.IntegerField(db_column='maxTokens')
    top_p = models.FloatField(db_column='topP')
    top_k = models.FloatField(db_column='topK')
    status = models.IntegerField()  # 0-禁用, 1-启用
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'model_config'
        ordering = ['-create_at']
        verbose_name = '模型配置'
        verbose_name_plural = '模型配置'
    
    def __str__(self):
        return f"{self.provider_name} - {self.model_name}"


class CustomPrompt(models.Model):
    """自定义提示词模型（对应 Prisma CustomPrompts）"""
    id = models.CharField(max_length=255, primary_key=True, default=generate_id, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='custom_prompts', db_column='projectId')
    prompt_type = models.CharField(max_length=255, db_column='promptType')  # 提示词类型
    prompt_key = models.CharField(max_length=255, db_column='promptKey')  # 提示词键名
    language = models.CharField(max_length=10)  # 语言: zh-CN, en
    content = models.TextField()  # 自定义的提示词内容
    is_active = models.BooleanField(default=True, db_column='isActive')
    create_at = models.DateTimeField(default=timezone.now, db_column='createAt')
    update_at = models.DateTimeField(auto_now=True, db_column='updateAt')
    
    class Meta:
        db_table = 'custom_prompts'
        ordering = ['-create_at']
        unique_together = [['project', 'prompt_type', 'prompt_key', 'language']]
        indexes = [
            models.Index(fields=['project', 'prompt_type']),
            models.Index(fields=['project', 'language']),
        ]
        verbose_name = '自定义提示词'
        verbose_name_plural = '自定义提示词'
    
    def __str__(self):
        return f"{self.prompt_type} - {self.prompt_key} ({self.language})"
