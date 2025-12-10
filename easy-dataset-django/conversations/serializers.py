"""
多轮对话序列化器
"""
from rest_framework import serializers
from .models import DatasetConversation


class DatasetConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetConversation
        fields = '__all__'
        read_only_fields = ('id', 'create_at', 'update_at')
