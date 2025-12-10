"""
LLM序列化器
"""
from rest_framework import serializers
from .models import ModelConfig, CustomPrompt


class ModelConfigSerializer(serializers.ModelSerializer):
    """模型配置序列化器（对外统一使用驼峰字段）"""

    providerId = serializers.CharField(source='provider_id')
    providerName = serializers.CharField(source='provider_name')
    # 为前端调用（模型测试/聊天）提供明文；若需隐藏可再加开关
    apiKey = serializers.CharField(source='api_key')
    modelId = serializers.CharField(source='model_id')
    modelName = serializers.CharField(source='model_name')
    maxTokens = serializers.IntegerField(source='max_tokens')
    topP = serializers.FloatField(source='top_p')
    topK = serializers.FloatField(source='top_k')
    hasApiKey = serializers.SerializerMethodField()

    def get_hasApiKey(self, obj):
        return bool(obj.api_key)

    class Meta:
        model = ModelConfig
        fields = [
            'id', 'providerId', 'providerName', 'endpoint', 'apiKey',
            'modelId', 'modelName', 'type', 'temperature', 'maxTokens',
            'topP', 'topK', 'status', 'create_at', 'update_at',
            'hasApiKey'
        ]
        read_only_fields = ['id', 'create_at', 'update_at']


class ModelConfigCreateSerializer(serializers.ModelSerializer):
    """模型配置创建序列化器（驼峰字段）"""

    providerId = serializers.CharField(source='provider_id')
    providerName = serializers.CharField(source='provider_name')
    apiKey = serializers.CharField(source='api_key', write_only=True, required=False, allow_blank=True)
    modelId = serializers.CharField(source='model_id')
    modelName = serializers.CharField(source='model_name')
    maxTokens = serializers.IntegerField(source='max_tokens', required=False)
    topP = serializers.FloatField(source='top_p', required=False)
    topK = serializers.FloatField(source='top_k', required=False)

    class Meta:
        model = ModelConfig
        fields = [
            'providerId', 'providerName', 'endpoint', 'apiKey',
            'modelId', 'modelName', 'type', 'temperature', 'maxTokens',
            'topP', 'topK', 'status'
        ]


class CustomPromptSerializer(serializers.ModelSerializer):
    """自定义提示词序列化器"""
    
    class Meta:
        model = CustomPrompt
        fields = [
            'id', 'prompt_type', 'prompt_key', 'language', 'content',
            'create_at', 'update_at'
        ]
        read_only_fields = ['id', 'create_at', 'update_at']
