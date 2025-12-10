"""
问题序列化器
"""
from rest_framework import serializers
from .models import Question


class QuestionSerializer(serializers.ModelSerializer):
    """问题序列化器"""
    chunk_name = serializers.CharField(source='chunk.name', read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'chunk_id', 'chunk_name', 'ga_pair_id', 'question', 'label',
            'answered', 'image_id', 'image_name', 'template_id',
            'create_at', 'update_at'
        ]
        read_only_fields = ['id', 'create_at', 'update_at']


class QuestionCreateSerializer(serializers.ModelSerializer):
    """问题创建序列化器"""
    
    class Meta:
        model = Question
        fields = [
            'chunk_id', 'ga_pair_id', 'question', 'label',
            'answered', 'image_id', 'image_name', 'template_id'
        ]
    
    def validate_chunk_id(self, value):
        """验证文本块ID"""
        if not value:
            raise serializers.ValidationError('文本块ID不能为空')
        return value

