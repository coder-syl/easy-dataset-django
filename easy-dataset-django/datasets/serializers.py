"""
数据集序列化器
"""
from rest_framework import serializers
from .models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    """数据集序列化器"""
    
    class Meta:
        model = Dataset
        fields = [
            'id', 'question_id', 'question', 'answer', 'answer_type',
            'chunk_name', 'chunk_content', 'model', 'question_label',
            'cot', 'confirmed', 'score', 'ai_evaluation', 'tags', 'note',
            'other', 'create_at', 'update_at'
        ]
        read_only_fields = ['id', 'create_at', 'update_at']


class DatasetCreateSerializer(serializers.ModelSerializer):
    """数据集创建序列化器"""
    
    class Meta:
        model = Dataset
        fields = [
            'question_id', 'question', 'answer', 'answer_type',
            'chunk_name', 'chunk_content', 'model', 'question_label',
            'cot', 'confirmed', 'score', 'ai_evaluation', 'tags', 'note', 'other'
        ]

