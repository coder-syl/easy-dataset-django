"""
文件序列化器
"""
from rest_framework import serializers
from .models import UploadFile


class UploadFileSerializer(serializers.ModelSerializer):
    """文件序列化器"""
    
    class Meta:
        model = UploadFile
        fields = [
            'id', 'file_name', 'file_ext', 'path', 'size', 'md5',
            'create_at', 'update_at'
        ]
        read_only_fields = ['id', 'create_at', 'update_at']

