# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： config_views.py
    @date：2024/12/19 16:00
    @desc: 配置管理视图
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.core.paginator import Paginator
from application.models.config import SystemConfig, ConfigManager
from application.serializers.config_serializer import (
    SystemConfigSerializer, SystemConfigCreateSerializer,
    SystemConfigUpdateSerializer, SystemConfigListSerializer
)


class SystemConfigViewSet(APIView):
    """系统配置视图集"""
    
    permission_classes = [AllowAny]  # 暂时允许匿名访问
    
    def get(self, request):
        """获取配置列表"""
        try:
            # 获取查询参数
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            search = request.GET.get('search', '')
            is_active = request.GET.get('is_active', '')
            
            # 构建查询
            queryset = SystemConfig.objects.all()
            
            # 搜索过滤
            if search:
                queryset = queryset.filter(
                    Q(key__icontains=search) | 
                    Q(value__icontains=search) | 
                    Q(description__icontains=search)
                )
            
            # 状态过滤
            if is_active != '':
                is_active_bool = is_active.lower() == 'true'
                queryset = queryset.filter(is_active=is_active_bool)
            
            # 分页
            paginator = Paginator(queryset, page_size)
            configs = paginator.get_page(page)
            
            # 序列化
            serializer = SystemConfigListSerializer(configs, many=True)
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': {
                    'list': serializer.data,
                    'total': paginator.count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages
                }
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'获取配置列表失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """创建配置"""
        try:
            serializer = SystemConfigCreateSerializer(data=request.data)
            if serializer.is_valid():
                config = serializer.save()
                
                # 清除缓存
                ConfigManager.clear_cache(config.key)
                
                return Response({
                    'code': 200,
                    'message': '创建成功',
                    'data': SystemConfigSerializer(config).data
                })
            else:
                return Response({
                    'code': 400,
                    'message': '创建失败',
                    'data': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'创建配置失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SystemConfigDetailView(APIView):
    """系统配置详情视图"""
    
    permission_classes = [AllowAny]  # 暂时允许匿名访问
    
    def get(self, request, config_id):
        """获取配置详情"""
        try:
            config = SystemConfig.objects.get(id=config_id)
            serializer = SystemConfigSerializer(config)
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': serializer.data
            })
            
        except SystemConfig.DoesNotExist:
            return Response({
                'code': 404,
                'message': '配置不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'获取配置详情失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, config_id):
        """更新配置"""
        try:
            config = SystemConfig.objects.get(id=config_id)
            serializer = SystemConfigUpdateSerializer(config, data=request.data, partial=True)
            
            if serializer.is_valid():
                config = serializer.save()
                
                # 清除缓存
                ConfigManager.clear_cache(config.key)
                
                return Response({
                    'code': 200,
                    'message': '更新成功',
                    'data': SystemConfigSerializer(config).data
                })
            else:
                return Response({
                    'code': 400,
                    'message': '更新失败',
                    'data': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except SystemConfig.DoesNotExist:
            return Response({
                'code': 404,
                'message': '配置不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'更新配置失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, config_id):
        """删除配置（软删除）"""
        try:
            config = SystemConfig.objects.get(id=config_id)
            config.is_active = False
            config.save()
            
            # 清除缓存
            ConfigManager.clear_cache(config.key)
            
            return Response({
                'code': 200,
                'message': '删除成功',
                'data': None
            })
            
        except SystemConfig.DoesNotExist:
            return Response({
                'code': 404,
                'message': '配置不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'删除配置失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])  # 暂时允许匿名访问
def get_config_by_key(request, key):
    """根据键获取配置"""
    try:
        value = ConfigManager.get_config(key)
        
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': {
                'key': key,
                'value': value
            }
        })
        
    except Exception as e:
        return Response({
            'code': 500,
            'message': f'获取配置失败: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # 暂时允许匿名访问
def set_config_by_key(request):
    """根据键设置配置"""
    try:
        key = request.data.get('key')
        value = request.data.get('value')
        description = request.data.get('description', '')
        
        if not key:
            return Response({
                'code': 400,
                'message': '键不能为空',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 设置配置
        ConfigManager.set_config(key, value, description)
        
        return Response({
            'code': 200,
            'message': '设置成功',
            'data': {
                'key': key,
                'value': value
            }
        })
        
    except Exception as e:
        return Response({
            'code': 500,
            'message': f'设置配置失败: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])  # 暂时允许匿名访问
def get_all_configs(request):
    """获取所有配置"""
    try:
        configs = ConfigManager.get_all_configs()
        
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': configs
        })
        
    except Exception as e:
        return Response({
            'code': 500,
            'message': f'获取所有配置失败: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # 暂时允许匿名访问
def clear_cache(request):
    """清除配置缓存"""
    try:
        key = request.data.get('key')
        
        if key:
            ConfigManager.clear_cache(key)
            message = f'清除缓存成功: {key}'
        else:
            ConfigManager.clear_cache()
            message = '清除所有缓存成功'
        
        return Response({
            'code': 200,
            'message': message,
            'data': None
        })
        
    except Exception as e:
        return Response({
            'code': 500,
            'message': f'清除缓存失败: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 