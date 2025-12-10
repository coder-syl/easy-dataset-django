"""
文本块序列化器
"""
from rest_framework import serializers
from .models import Chunk


class ChunkSerializer(serializers.ModelSerializer):
    """文本块序列化器"""
    
    class Meta:
        model = Chunk
        fields = [
            'id', 'name', 'file_id', 'file_name', 'content', 'summary', 'size',
            'create_at', 'update_at'
        ]
        read_only_fields = ['id', 'create_at', 'update_at']

