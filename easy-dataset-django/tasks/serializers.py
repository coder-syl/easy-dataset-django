"""
任务序列化器
"""
from rest_framework import serializers
from .models import Task
import json


class TaskSerializer(serializers.ModelSerializer):
    """任务序列化器（输出驼峰）"""
    modelInfo = serializers.SerializerMethodField()
    totalCount = serializers.IntegerField(source='total_count')
    completedCount = serializers.IntegerField(source='completed_count')
    taskType = serializers.CharField(source='task_type')
    note = serializers.SerializerMethodField()
    startTime = serializers.DateTimeField(source='start_time', read_only=True)
    endTime = serializers.DateTimeField(source='end_time', read_only=True, allow_null=True)
    createAt = serializers.DateTimeField(source='create_at', read_only=True)
    updateAt = serializers.DateTimeField(source='update_at', read_only=True)
    errorCount = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'taskType', 'status', 'modelInfo', 'language',
            'detail', 'totalCount', 'completedCount', 'note',
            'startTime', 'endTime', 'createAt', 'updateAt', 'errorCount'
        ]
        read_only_fields = ['id', 'create_at', 'update_at']

    def get_modelInfo(self, obj):
        """解析model_info JSON字符串"""
        try:
            return json.loads(obj.model_info or '{}')
        except Exception:
            return {}

    def get_note(self, obj):
        """解析note JSON字符串"""
        try:
            return json.loads(obj.note or '{}')
        except Exception:
            return {}
    
    def get_errorCount(self, obj):
        """从detail中提取错误数量"""
        try:
            if obj.detail:
                detail_data = json.loads(obj.detail) if isinstance(obj.detail, str) else obj.detail
                if isinstance(detail_data, dict) and 'errorList' in detail_data:
                    return len(detail_data.get('errorList', []))
        except Exception:
            pass
        return 0


class TaskCreateSerializer(serializers.ModelSerializer):
    """任务创建序列化器（接受驼峰入参）"""

    taskType = serializers.CharField(source='task_type')
    modelInfo = serializers.JSONField(source='model_info', required=False)
    language = serializers.CharField(required=False, allow_blank=True)
    detail = serializers.CharField(required=False, allow_blank=True)
    totalCount = serializers.IntegerField(source='total_count', required=False)
    note = serializers.JSONField(required=False)

    class Meta:
        model = Task
        fields = [
            'taskType', 'modelInfo', 'language',
            'detail', 'totalCount', 'note'
        ]

