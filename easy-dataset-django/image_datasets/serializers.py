"""
图像数据集序列化器
"""
from rest_framework import serializers
from .models import ImageDataset


class ImageDatasetSerializer(serializers.ModelSerializer):
    """图像数据集序列化器"""
    
    image_id = serializers.CharField(source='image.id', read_only=True)
    
    class Meta:
        model = ImageDataset
        fields = [
            'id', 'image_id', 'image_name', 'question', 'answer', 'answer_type',
            'score', 'tags', 'note', 'confirmed',
            'create_at', 'update_at'
        ]
        read_only_fields = ['id', 'create_at', 'update_at']


class ImageDatasetCreateSerializer(serializers.ModelSerializer):
    """图像数据集创建序列化器"""
    
    class Meta:
        model = ImageDataset
        fields = [
            'image_id', 'image_name', 'question', 'answer', 'answer_type',
            'score', 'tags', 'note', 'confirmed'
        ]

