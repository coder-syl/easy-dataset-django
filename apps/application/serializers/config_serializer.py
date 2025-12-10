# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： config_serializer.py
    @date：2024/12/19 16:00
    @desc: 配置管理序列化器
"""

from rest_framework import serializers
from application.models.config import SystemConfig


class SystemConfigSerializer(serializers.ModelSerializer):
    """系统配置序列化器"""
    
    typed_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemConfig
        fields = [
            'id', 'key', 'value', 'description', 'is_active',
            'created_at', 'updated_at', 'typed_value'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_typed_value(self, obj):
        """获取类型转换后的值"""
        return obj.get_typed_value()
    
    def validate_key(self, value):
        """验证配置键"""
        if not value:
            raise serializers.ValidationError("配置键不能为空")
        
        # 检查键名格式
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("配置键只能包含字母、数字、下划线和连字符")
        
        # 检查是否已存在（排除当前实例）
        instance = self.instance
        if instance:
            if SystemConfig.objects.filter(key=value).exclude(id=instance.id).exists():
                raise serializers.ValidationError("配置键已存在")
        else:
            if SystemConfig.objects.filter(key=value).exists():
                raise serializers.ValidationError("配置键已存在")
        
        return value


class SystemConfigCreateSerializer(serializers.ModelSerializer):
    """系统配置创建序列化器"""
    
    class Meta:
        model = SystemConfig
        fields = ['key', 'value', 'description', 'is_active']
    
    def validate_key(self, value):
        """验证配置键"""
        if not value:
            raise serializers.ValidationError("配置键不能为空")
        
        if SystemConfig.objects.filter(key=value).exists():
            raise serializers.ValidationError("配置键已存在")
        
        return value


class SystemConfigUpdateSerializer(serializers.ModelSerializer):
    """系统配置更新序列化器"""
    
    class Meta:
        model = SystemConfig
        fields = ['value', 'description', 'is_active']


class SystemConfigListSerializer(serializers.ModelSerializer):
    """系统配置列表序列化器"""
    
    typed_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemConfig
        fields = [
            'id', 'key', 'value', 'typed_value', 'description', 
            'is_active', 'created_at', 'updated_at'
        ]
    
    def get_typed_value(self, obj):
        """获取类型转换后的值"""
        return obj.get_typed_value() 