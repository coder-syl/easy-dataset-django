# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： config.py
    @date：2024/12/19 16:00
    @desc: 通用配置管理模型
"""

import json
import logging
from typing import Any, Dict, Optional
from django.db import models
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SystemConfig(models.Model):
    """系统配置模型"""
    
    key = models.CharField(max_length=100, unique=True, verbose_name='配置键')
    value = models.TextField(verbose_name='配置值')
    description = models.TextField(blank=True, null=True, verbose_name='配置描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'system_config'
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'
        ordering = ['key']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.key}: {self.value}"
    
    def get_typed_value(self) -> Any:
        """尝试将值转换为适当的数据类型"""
        if not self.value:
            return None
            
        try:
            # 尝试转换为JSON
            return json.loads(self.value)
        except (ValueError, json.JSONDecodeError):
            # 如果不是JSON，尝试其他类型
            value = self.value.strip()
            
            # 尝试布尔值
            if value.lower() in ('true', 'false', '1', '0', 'yes', 'no'):
                return value.lower() in ('true', '1', 'yes')
            
            # 尝试整数
            try:
                return int(value)
            except ValueError:
                pass
            
            # 尝试浮点数
            try:
                return float(value)
            except ValueError:
                pass
            
            # 返回字符串
            return value


class ConfigManager:
    """配置管理器"""
    
    CACHE_PREFIX = 'system_config:'
    CACHE_TIMEOUT = 300  # 5分钟缓存
    
    @classmethod
    def get_config(cls, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        :param key: 配置键
        :param default: 默认值
        :return: 配置值
        """
        # 尝试从缓存获取
        cached_value = cache.get(f"{cls.CACHE_PREFIX}{key}")
        if cached_value is not None:
            return cached_value
        
        try:
            config = SystemConfig.objects.get(key=key, is_active=True)
            value = config.get_typed_value()
            
            # 设置缓存
            cache.set(f"{cls.CACHE_PREFIX}{key}", value, cls.CACHE_TIMEOUT)
            
            return value
        except SystemConfig.DoesNotExist:
            logger.warning(f"配置不存在: {key}")
            return default
        except Exception as e:
            logger.error(f"获取配置失败: {key}, 错误: {e}")
            return default
    
    @classmethod
    def set_config(cls, key: str, value: Any, description: str = '') -> bool:
        """
        设置配置值
        
        :param key: 配置键
        :param value: 配置值
        :param description: 配置描述
        :return: 是否成功
        """
        try:
            # 将值转换为字符串存储
            if isinstance(value, (dict, list)):
                str_value = json.dumps(value, ensure_ascii=False)
            else:
                str_value = str(value)
            
            config, created = SystemConfig.objects.get_or_create(
                key=key,
                defaults={
                    'value': str_value,
                    'description': description,
                }
            )
            
            if not created:
                config.value = str_value
                config.description = description
                config.is_active = True
                config.save()
            
            # 清除缓存
            cache.delete(f"{cls.CACHE_PREFIX}{key}")
            
            logger.info(f"配置已更新: {key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"设置配置失败: {key}, 错误: {e}")
            return False
    
    @classmethod
    def delete_config(cls, key: str) -> bool:
        """
        删除配置
        
        :param key: 配置键
        :return: 是否成功
        """
        try:
            config = SystemConfig.objects.get(key=key)
            config.is_active = False
            config.save()
            
            # 清除缓存
            cache.delete(f"{cls.CACHE_PREFIX}{key}")
            
            logger.info(f"配置已删除: {key}")
            return True
            
        except SystemConfig.DoesNotExist:
            logger.warning(f"配置不存在: {key}")
            return False
        except Exception as e:
            logger.error(f"删除配置失败: {key}, 错误: {e}")
            return False
    
    @classmethod
    def get_all_configs(cls) -> Dict[str, Any]:
        """
        获取所有配置
        
        :return: 配置字典
        """
        try:
            configs = SystemConfig.objects.filter(is_active=True)
            
            result = {}
            for config in configs:
                result[config.key] = config.get_typed_value()
            
            return result
            
        except Exception as e:
            logger.error(f"获取所有配置失败: {e}")
            return {}
    
    @classmethod
    def clear_cache(cls, key: str = None) -> None:
        """
        清除缓存
        
        :param key: 配置键，如果为None则清除所有缓存
        """
        if key:
            cache.delete(f"{cls.CACHE_PREFIX}{key}")
        else:
            # 清除所有配置缓存
            cache.delete_pattern(f"{cls.CACHE_PREFIX}*")


# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """获取配置的便捷函数"""
    return ConfigManager.get_config(key, default)


def set_config(key: str, value: Any, description: str = '') -> bool:
    """设置配置的便捷函数"""
    return ConfigManager.set_config(key, value, description)


def delete_config(key: str) -> bool:
    """删除配置的便捷函数"""
    return ConfigManager.delete_config(key) 