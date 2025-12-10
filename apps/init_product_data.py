#!/usr/bin/env python
# coding=utf-8
"""
初始化产品数据
"""

import os
import sys
import django
from datetime import datetime

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartdoc.settings')
django.setup()

from application.models.business import Product


def init_product_data():
    """初始化产品数据"""
    
    # 检查是否已有数据
    if Product.objects.exists():
        print("产品数据已存在，跳过初始化")
        return
    
    products = [
        {
            'product_name': '金融产品推荐',
            'product_type': '个人贷款',
            'product_description': '根据客户风险画像和偏好，为客户推荐最适合的金融产品',
            'min_amount': 10000,
            'max_amount': 500000,
            'min_term_months': 12,
            'max_term_months': 60,
            'min_interest_rate': 3.5,
            'max_interest_rate': 8.5,
            'min_age': 18,
            'max_age': 65,
            'risk_level': 'medium',
            'target_customers': '工薪阶层，小微企业主',
            'service_region': '全国',
            'online_application': True,
            'online_approval': True,
            'online_disbursement': True,
            'online_repayment': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        },
        {
            'product_name': '企业经营贷',
            'product_type': '企业贷款',
            'product_description': '为中小企业提供经营资金支持，灵活还款方式',
            'min_amount': 50000,
            'max_amount': 2000000,
            'min_term_months': 6,
            'max_term_months': 36,
            'min_interest_rate': 4.0,
            'max_interest_rate': 12.0,
            'min_age': 22,
            'max_age': 60,
            'risk_level': 'high',
            'target_customers': '中小企业，个体工商户',
            'service_region': '全国',
            'online_application': True,
            'online_approval': False,
            'online_disbursement': True,
            'online_repayment': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        },
        {
            'product_name': '信用卡分期',
            'product_type': '信用卡',
            'product_description': '消费分期服务，购物更轻松',
            'min_amount': 1000,
            'max_amount': 50000,
            'min_term_months': 3,
            'max_term_months': 24,
            'min_interest_rate': 0.5,
            'max_interest_rate': 1.5,
            'min_age': 18,
            'max_age': 70,
            'risk_level': 'low',
            'target_customers': '信用卡持卡人',
            'service_region': '全国',
            'online_application': True,
            'online_approval': True,
            'online_disbursement': True,
            'online_repayment': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        },
        {
            'product_name': '稳健理财',
            'product_type': '理财产品',
            'product_description': '低风险，稳定收益的理财产品',
            'min_amount': 1000,
            'max_amount': 1000000,
            'min_term_months': 1,
            'max_term_months': 12,
            'min_interest_rate': 2.8,
            'max_interest_rate': 4.2,
            'min_age': 18,
            'max_age': 80,
            'risk_level': 'low',
            'target_customers': '保守型投资者',
            'service_region': '全国',
            'online_application': True,
            'online_approval': True,
            'online_disbursement': True,
            'online_repayment': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        },
        {
            'product_name': '意外保险',
            'product_type': '保险产品',
            'product_description': '意外伤害保险，保障您的安全',
            'min_amount': 100,
            'max_amount': 10000,
            'min_term_months': 12,
            'max_term_months': 12,
            'min_interest_rate': None,
            'max_interest_rate': None,
            'min_age': 0,
            'max_age': 80,
            'risk_level': 'low',
            'target_customers': '所有人群',
            'service_region': '全国',
            'online_application': True,
            'online_approval': True,
            'online_disbursement': True,
            'online_repayment': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        }
    ]
    
    for product_data in products:
        Product.objects.create(**product_data)
        print(f"创建产品: {product_data['product_name']}")
    
    print(f"成功创建 {len(products)} 个产品")


if __name__ == '__main__':
    init_product_data() 