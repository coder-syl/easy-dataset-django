"""
标签序列化器
"""
from rest_framework import serializers
from .models import Tag


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""
    
    class Meta:
        model = Tag
        fields = ['id', 'label', 'parent_id', 'create_at', 'update_at']
        read_only_fields = ['id', 'create_at', 'update_at']


class TagCreateSerializer(serializers.ModelSerializer):
    """标签创建序列化器"""
    
    class Meta:
        model = Tag
        fields = ['project', 'label', 'parent_id']

