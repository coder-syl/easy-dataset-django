#!/usr/bin/env python
"""
为现有客户添加身份证号
"""

import os
import sys
import django

# 设置Django环境
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartdoc.settings")
django.setup()

from application.models.business import Customer, CustomerLoan

def update_customer_cert_id():
    """为现有客户添加身份证号"""
    print("=== 为现有客户添加身份证号 ===")
    
    # 获取所有客户
    customers = Customer.objects.all()
    print(f"总客户数: {customers.count()}")
    
    # 为每个客户添加身份证号（示例）
    for i, customer in enumerate(customers, 1):
        if not customer.cert_id:
            # 生成示例身份证号（实际应用中应该从真实数据获取）
            cert_id = f"32082119900101{1000 + i:04d}"
            customer.cert_id = cert_id
            customer.save()
            print(f"客户 {i}: {customer.name}, 地址: {customer.household_address} -> 身份证号: {customer.cert_id}")
        else:
            print(f"客户 {i}: {customer.name} -> 已有身份证号: {customer.cert_id}")
    
    # 显示所有客户信息
    print(f"\n=== 客户信息 ===")
    for customer in customers:
        print(f"ID: {customer.id}, 姓名: {customer.name}, 身份证号: {customer.cert_id}")
    
    # 显示贷款记录
    print(f"\n=== 贷款记录 ===")
    loans = CustomerLoan.objects.all()
    for i, loan in enumerate(loans, 1):
        print(f"贷款记录 {i}:")
        print(f"  - 客户姓名: {loan.customer_name}")
        print(f"  - 身份证号: {loan.cert_id}")
        print(f"  - 产品: {loan.product_name}")
        print(f"  - 金额: {loan.loan_amount}")
        print(f"  - 状态: {loan.loan_status}")

if __name__ == "__main__":
    update_customer_cert_id() 