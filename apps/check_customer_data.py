#!/usr/bin/env python
"""
检查数据库中的客户数据
"""

import os
import sys
import django

# 设置Django环境
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartdoc.settings")
django.setup()

from application.models.business import Customer, Product, CustomerRiskProfile  # , CustomerPreference

def check_customer_data():
    """检查客户数据"""
    print("=== 检查数据库中的客户数据 ===")
    
    # 检查所有客户
    # 注释掉批量获取客户的地方，提示需通过get_customer_from_third_party单独获取。
    # customers = Customer.objects.all()
    # print(f"总客户数: {customers.count()}")
    
    # if customers.count() > 0:
    #     print("\n客户列表:")
    #     for customer in customers:
    #         # 推荐相关字段替换
    #         # name, cert_id, gender, age, marital_status, education_level, household_address, ...
    #         # 其他无对应字段的注释掉
    #         # 例如：
    #         # print(f"ID: {customer.id}, 姓名: {customer.name}, 地址: {customer.household_address}")
    #         # ...

    #         # 具体替换如下：
    #         # - customer.cert_id 保留
    #         # - customer.address -> customer.household_address
    #         # - customer.company_type -> employer_name
    #         # - customer.occupation -> occupation_type
    #         # - customer.monthly_income -> float(customer.annual_income)/12 if customer.annual_income else None
    #         # - customer.yearly_income -> customer.annual_income
    #         # - customer.income_source -> main_income_source
    #         # - customer.family_monthly_income 保留
    #         # - customer.family_yearly_income -> customer.family_annual_income
    #         # - customer.total_assets -> customer.family_assets
    #         # - customer.total_liabilities -> customer.family_debt
    #         # - customer.net_assets -> customer.family_net_assets
    #         # - customer.house_property -> customer.residence_type
    #         # - 其他无对应字段全部注释

    #         # 替换打印客户信息
    #         # print(f"ID: {customer.id}, 姓名: {customer.name}, 年龄: {customer.age}")
    #         print(f"ID: {customer.id}, 姓名: {customer.name}, 地址: {customer.household_address}, 年龄: {customer.age}")
            
    #         # 检查是否有风险画像
    #         try:
    #             risk_profile = CustomerRiskProfile.objects.get(customer=customer)
    #             print(f"  - 风险画像: {risk_profile.risk_level}, 信用分: {risk_profile.credit_score}")
    #         except CustomerRiskProfile.MultipleObjectsReturned:
    #             print(f"  - 风险画像异常: 存在多条，默认取第一条")
    #             risk_profile = CustomerRiskProfile.objects.filter(customer=customer).first()
    #             if risk_profile:
    #                 print(f"  - 风险画像: {risk_profile.risk_level}, 信用分: {risk_profile.credit_score}")
    #             else:
    #                 print(f"  - 风险画像: 无")
    #         except CustomerRiskProfile.DoesNotExist:
    #             print(f"  - 风险画像: 无")
            
    #         # 检查客户偏好数据
    #         # try:
    #         #     preference = CustomerPreference.objects.get(customer=customer)
    #         #     print(f"客户偏好: 期限{preference.preferred_term_months}个月, 金额{preference.preferred_amount}, 风险承受度{preference.risk_tolerance}")
    #         # except CustomerPreference.DoesNotExist:
    #         #     print("该客户没有偏好设置")
    # else:
    #     print("没有找到任何客户数据")
    
    # 检查产品数据
    products = Product.objects.all()
    print(f"\n总产品数: {products.count()}")
    
    if products.count() > 0:
        print("\n产品列表:")
        for product in products:
            print(f"ID: {product.id}, 名称: {product.product_name}, 类型: {product.product_type}")
    
    # 特别检查ID为1的客户
    print(f"\n=== 特别检查ID为1的客户 ===")
    try:
        customer_1 = Customer.objects.get(id=1)
        print(f"找到客户ID=1: {customer_1.name}")
        print(f"详细信息: {customer_1.__dict__}")
    except Customer.DoesNotExist:
        print("没有找到ID为1的客户")
        print("可用的客户ID:")
        # 注释掉批量获取客户的地方，提示需通过get_customer_from_third_party单独获取。
        # available_ids = Customer.objects.values_list('id', flat=True)
        # print(list(available_ids))

if __name__ == "__main__":
    check_customer_data() 