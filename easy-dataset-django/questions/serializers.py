"""
问题序列化器
"""
from rest_framework import serializers
from .models import Question, QuestionTemplate
import json


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
    # Django REST Framework 的 ModelSerializer 会自动为 ForeignKey 字段创建 {field}_id 字段
    # 对于模型的 chunk 字段（ForeignKey），会自动创建 chunk_id 字段
    # 但我们显式定义以确保它是必需的
    # 注意：DRF 会自动将 chunk_id 映射到模型的 chunk ForeignKey 字段
    chunk_id = serializers.CharField(required=True, allow_blank=False, allow_null=False)
    
    class Meta:
        model = Question
        fields = [
            'chunk_id', 'ga_pair_id', 'question', 'label',
            'answered', 'image_id', 'image_name', 'template_id'
        ]
    
    def validate_chunk_id(self, value):
        """验证文本块ID"""
        # 检查是否为 None、空字符串或只包含空白字符
        if not value or (isinstance(value, str) and not value.strip()):
            raise serializers.ValidationError('文本块ID不能为空')
        return value
    
    def validate(self, attrs):
        """验证整个对象"""
        # 确保 chunk_id 存在且不为空
        chunk_id = attrs.get('chunk_id')
        if not chunk_id or (isinstance(chunk_id, str) and not chunk_id.strip()):
            raise serializers.ValidationError({'chunk_id': '文本块ID不能为空'})
        
        # 验证 chunk 是否存在
        from chunks.models import Chunk
        project = self.context.get('project')
        if project:
            try:
                Chunk.objects.get(id=chunk_id, project=project)
            except Chunk.DoesNotExist:
                raise serializers.ValidationError({'chunk_id': '文本块不存在'})
        
        return attrs
    
    def create(self, validated_data):
        """创建问题，确保 chunk_id 正确映射到 chunk 字段"""
        # Django REST Framework 会自动将 chunk_id 转换为 chunk 对象
        # 但我们需要确保 chunk_id 存在
        chunk_id = validated_data.get('chunk_id')
        if not chunk_id:
            raise serializers.ValidationError({'chunk_id': '文本块ID不能为空'})
        
        # DRF 会自动处理 chunk_id -> chunk 的映射
        # 但为了确保正确，我们显式验证并设置
        from chunks.models import Chunk
        project = validated_data.get('project') or self.context.get('project')
        if project:
            try:
                chunk = Chunk.objects.get(id=chunk_id, project=project)
                # 显式设置 chunk 字段，确保正确映射
                validated_data['chunk'] = chunk
                # 移除 chunk_id，因为我们已经设置了 chunk 对象
                validated_data.pop('chunk_id', None)
            except Chunk.DoesNotExist:
                raise serializers.ValidationError({'chunk_id': '文本块不存在'})
        
        # 创建问题
        return super().create(validated_data)


class QuestionTemplateSerializer(serializers.ModelSerializer):
    """问题模板序列化器（使用 snake_case 格式，符合 Django 编码风格）"""
    project_id = serializers.CharField(source='project.id', read_only=True)
    create_at = serializers.DateTimeField(read_only=True)
    update_at = serializers.DateTimeField(read_only=True)
    labels = serializers.SerializerMethodField()
    usage_count = serializers.IntegerField(read_only=True, default=0)
    
    class Meta:
        model = QuestionTemplate
        fields = [
            'id', 'project_id', 'question', 'source_type', 'answer_type',
            'description', 'labels', 'custom_format', 'order',
            'create_at', 'update_at', 'usage_count'
        ]
        read_only_fields = ['id', 'create_at', 'update_at']
        extra_kwargs = {
            'source_type': {'required': True},
            'answer_type': {'required': True},
            'custom_format': {'required': False, 'allow_blank': True}
        }
    
    def get_labels(self, obj):
        """解析 labels JSON 字符串"""
        if obj.labels:
            try:
                return json.loads(obj.labels)
            except:
                return []
        return []
    
    def to_representation(self, instance):
        """将输出字段转换为 snake_case 格式（处理 custom_format 的 JSON 解析）"""
        data = super().to_representation(instance)
        # 处理 custom_format 的 JSON 解析
        if 'custom_format' in data and data['custom_format']:
            try:
                data['custom_format'] = json.loads(data['custom_format'])
            except:
                pass  # 如果不是 JSON，保持原样
        return data
    
    def to_internal_value(self, data):
        """将输入数据转换为内部值（前端已使用 snake_case，无需转换）"""
        # 处理 labels（可能是列表或字符串）
        data_copy = data.copy() if hasattr(data, 'copy') else dict(data)
        
        if 'labels' in data_copy:
            labels = data_copy['labels']
            if isinstance(labels, str):
                try:
                    # 如果是 JSON 字符串，解析它
                    labels = json.loads(labels)
                except:
                    labels = []
            if not isinstance(labels, list):
                labels = []
            data_copy['labels'] = labels
        
        return super().to_internal_value(data_copy)
    
    def create(self, validated_data):
        """创建模板，处理 JSON 字段"""
        # 序列化 labels
        labels = validated_data.get('labels', [])
        if isinstance(labels, list):
            validated_data['labels'] = json.dumps(labels, ensure_ascii=False)
        else:
            validated_data['labels'] = ''
        
        # 序列化 customFormat
        custom_format = validated_data.get('custom_format', None)
        if custom_format:
            if isinstance(custom_format, dict) or isinstance(custom_format, list):
                validated_data['custom_format'] = json.dumps(custom_format, ensure_ascii=False)
            elif isinstance(custom_format, str):
                # 如果已经是字符串，尝试解析验证
                try:
                    json.loads(custom_format)  # 验证是否为有效 JSON
                    validated_data['custom_format'] = custom_format
                except:
                    validated_data['custom_format'] = custom_format
            else:
                validated_data['custom_format'] = str(custom_format)
        else:
            validated_data['custom_format'] = ''
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """更新模板，处理 JSON 字段"""
        # 序列化 labels
        if 'labels' in validated_data:
            labels = validated_data['labels']
            if isinstance(labels, list):
                validated_data['labels'] = json.dumps(labels, ensure_ascii=False)
            else:
                validated_data['labels'] = ''
        
        # 序列化 customFormat
        if 'custom_format' in validated_data:
            custom_format = validated_data['custom_format']
            if custom_format:
                if isinstance(custom_format, dict) or isinstance(custom_format, list):
                    validated_data['custom_format'] = json.dumps(custom_format, ensure_ascii=False)
                elif isinstance(custom_format, str):
                    # 如果已经是字符串，尝试解析验证
                    try:
                        json.loads(custom_format)  # 验证是否为有效 JSON
                        validated_data['custom_format'] = custom_format
                    except:
                        validated_data['custom_format'] = custom_format
                else:
                    validated_data['custom_format'] = str(custom_format)
            else:
                validated_data['custom_format'] = ''
        
        return super().update(instance, validated_data)

