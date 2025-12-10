"""
项目序列化器
"""
from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    """项目序列化器"""
    _count = serializers.SerializerMethodField(method_name='get_count')
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description',
            'global_prompt', 'question_prompt', 'answer_prompt',
            'label_prompt', 'domain_tree_prompt', 'clean_prompt',
            'default_model_config_id', 'test',
            'create_at', 'update_at', '_count'
        ]
        read_only_fields = ['id', 'create_at', 'update_at', '_count']
    
    def get_count(self, obj):
        """获取统计信息"""
        return {
            'Questions': obj.questions.count() if hasattr(obj, 'questions') else 0,
            'Datasets': obj.datasets.count() if hasattr(obj, 'datasets') else 0,
        }


class ProjectCreateSerializer(serializers.ModelSerializer):
    """项目创建序列化器"""
    
    class Meta:
        model = Project
        fields = [
            'name', 'description',
            'global_prompt', 'question_prompt', 'answer_prompt',
            'label_prompt', 'domain_tree_prompt', 'clean_prompt',
            'default_model_config_id', 'test'
        ]
    
    def validate_name(self, value):
        """验证项目名称"""
        if not value or not value.strip():
            raise serializers.ValidationError('项目名称不能为空')
        return value.strip()

