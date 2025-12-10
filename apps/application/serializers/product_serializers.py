# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： product_serializers.py
    @date：2024/12/19 10:00
    @desc: 产品相关序列化器
"""

from rest_framework import serializers
from application.models.business import Product


class ProductSerializer(serializers.ModelSerializer):
    """产品序列化器"""
    
    class Meta:
        model = Product
        fields = '__all__'
        
    def to_representation(self, instance):
        """自定义序列化输出"""
        data = super().to_representation(instance)
        
        # 添加一些计算字段或格式化字段
        if data.get('created_at'):
            data['created_at'] = instance.created_at.strftime('%Y-%m-%d %H:%M:%S') if instance.created_at else None
        if data.get('updated_at'):
            data['updated_at'] = instance.updated_at.strftime('%Y-%m-%d %H:%M:%S') if instance.updated_at else None
            
        # 为前端添加一些额外字段
        data['id'] = instance.id
        data['name'] = instance.product_name
        data['category'] = instance.product_type
        data['description'] = instance.product_description
        
        # 利率范围
        if instance.min_interest_rate and instance.max_interest_rate:
            data['interest_rate'] = f"{instance.min_interest_rate}%-{instance.max_interest_rate}%"
        elif instance.min_interest_rate:
            data['interest_rate'] = f"{instance.min_interest_rate}%"
        elif instance.max_interest_rate:
            data['interest_rate'] = f"{instance.max_interest_rate}%"
        else:
            data['interest_rate'] = None
            
        # 期限范围
        if instance.min_term_months and instance.max_term_months:
            data['term_months'] = f"{instance.min_term_months}-{instance.max_term_months}"
        elif instance.min_term_months:
            data['term_months'] = f"{instance.min_term_months}"
        elif instance.max_term_months:
            data['term_months'] = f"{instance.max_term_months}"
        else:
            data['term_months'] = None
            
        # 金额范围
        if instance.min_amount and instance.max_amount:
            data['price'] = instance.max_amount  # 使用最大金额作为price
            data['amount_range'] = f"{instance.min_amount}-{instance.max_amount}"
        elif instance.min_amount:
            data['price'] = instance.min_amount
            data['amount_range'] = f"{instance.min_amount}"
        elif instance.max_amount:
            data['price'] = instance.max_amount
            data['amount_range'] = f"{instance.max_amount}"
        else:
            data['price'] = None
            data['amount_range'] = None
            
        # 风险等级
        data['risk_level'] = instance.risk_level or 'medium'
        
        # 在线服务状态
        data['online_service'] = bool(instance.online_application and instance.online_approval)
        
        # 模拟状态字段（因为Product模型中没有status字段）
        data['status'] = 'active'  # 默认为活跃状态
        
        return data


class ProductQuerySerializer(serializers.Serializer):
    """产品查询参数序列化器"""
    name = serializers.CharField(required=False, allow_blank=True, help_text="产品名称")
    category = serializers.CharField(required=False, allow_blank=True, help_text="产品分类")
    status = serializers.CharField(required=False, allow_blank=True, help_text="产品状态")
    risk_level = serializers.CharField(required=False, allow_blank=True, help_text="风险等级")
    price_min = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, help_text="最小价格")
    price_max = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, help_text="最大价格") 