"""
图像序列化器
"""
from rest_framework import serializers
from .models import Image


class ImageSerializer(serializers.ModelSerializer):
    """图像序列化器"""
    
    class Meta:
        model = Image
        fields = [
            'id', 'image_name', 'path', 'size', 'width', 'height',
            'create_at', 'update_at'
        ]
        read_only_fields = ['id', 'create_at', 'update_at']

