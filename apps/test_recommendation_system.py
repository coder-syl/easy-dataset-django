#!/usr/bin/env python
"""
测试推荐系统是否正常工作
"""

import os
import sys
import django
from datetime import datetime, date

# 设置Django环境
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartdoc.settings")
django.setup()

from application.models.business import Customer, Product, CustomerLoan, CustomerRiskProfile
from application.recommendation.recommender import ProductRecommender

def test_recommendation_system():
    """测试推荐系统"""
    print("=== 测试推荐系统 ===")
    
    # 1. 检查是否有客户数据
    customers = Customer.objects.all()
    print(f"总客户数: {customers.count()}")
    
    if customers.count() == 0:
        print("没有客户数据，无法测试推荐系统")
        return
    
    # 2. 检查是否有产品数据
    products = Product.objects.all()
    print(f"总产品数: {products.count()}")
    
    if products.count() == 0:
        print("没有产品数据，无法测试推荐系统")
        return
    
    # 3. 检查是否有贷款数据
    loans = CustomerLoan.objects.all()
    print(f"总贷款记录数: {loans.count()}")
    
    # 4. 测试推荐系统
    customer = customers.first()
    # 推荐相关字段替换
    # name, cert_id, gender, age, marital_status, education_level, household_address, ...
    # 其他无对应字段的注释掉
    # 例如：
    # print(f"客户: {customer.name}, 地址: {customer.household_address}")
    # ...

    # 具体替换如下：
    # - customer.cert_id 保留
    # - customer.address -> customer.household_address
    # - customer.company_type -> employer_name
    # - customer.occupation -> occupation_type
    # - customer.monthly_income -> float(customer.annual_income)/12 if customer.annual_income else None
    # - customer.yearly_income -> customer.annual_income
    # - customer.income_source -> main_income_source
    # - customer.family_monthly_income 保留
    # - customer.family_yearly_income -> customer.family_annual_income
    # - customer.total_assets -> customer.family_assets
    # - customer.total_liabilities -> customer.family_debt
    # - customer.net_assets -> customer.family_net_assets
    # - customer.house_property -> customer.residence_type
    # - 其他无对应字段全部注释

    # 替换打印客户信息
    # print(f"\n测试客户: {customer.name} (ID: {customer.id})")
    print(f"\n测试客户: {customer.name}, 地址: {customer.household_address} (ID: {customer.id})")
    
    # 获取客户风险画像
    try:
        risk_profile = CustomerRiskProfile.objects.get(customer=customer)
        print(f"客户风险画像: {risk_profile.risk_level}")
    except CustomerRiskProfile.MultipleObjectsReturned:
        risk_profile = CustomerRiskProfile.objects.filter(customer=customer).first()
        print(f"客户有多个风险画像，使用第一个: {risk_profile.risk_level}")
    except CustomerRiskProfile.DoesNotExist:
        risk_profile = None
        print("客户无风险画像")
    
    # 获取客户贷款历史
    customer_loans = CustomerLoan.objects.filter(cert_id=customer.cert_id)
    print(f"客户贷款记录数: {customer_loans.count()}")
    
    # 显示贷款详情
    for i, loan in enumerate(customer_loans, 1):
        print(f"贷款记录 {i}:")
        print(f"  - 产品: {loan.product_name}")
        print(f"  - 金额: {loan.loan_amount}")
        print(f"  - 利率: {loan.leading_rate}%")
        print(f"  - 状态: {loan.loan_status}")
        print(f"  - 余额: {loan.balance}")
    
    # 5. 运行推荐系统
    try:
        recommender = ProductRecommender()
        result = recommender.recommend_products(
            customer=customer,
            products=products,
            customer_risk_profile=risk_profile,
            customer_preferences=None,
            interaction_history=[],
            customer_loans=list(customer_loans),
            top_n=3
        )
        
        print(f"\n推荐系统结果:")
        print(f"状态: {result.get('status')}")
        
        if result.get('status') == 'success':
            recommendations = result.get('recommendations', [])
            print(f"推荐产品数: {len(recommendations)}")
            
            for i, rec in enumerate(recommendations, 1):
                product = rec['product']
                score = rec['score']
                reason = rec['reason']
                print(f"\n推荐产品 {i}:")
                print(f"  - 产品名称: {product['product_name']}")
                print(f"  - 产品类型: {product['product_type']}")
                print(f"  - 推荐分数: {score}")
                print(f"  - 推荐理由: {reason}")
        else:
            print(f"推荐失败: {result.get('reason')}")
            
    except Exception as e:
        print(f"推荐系统测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def test_loan_history_recommender():
    """测试贷款历史推荐器"""
    print("\n=== 测试贷款历史推荐器 ===")
    
    from application.recommendation.recommender import LoanHistoryRecommender
    
    # 获取测试数据
    customer = Customer.objects.first()
    products = Product.objects.all()
    customer_loans = CustomerLoan.objects.filter(cert_id=customer.cert_id)
    
    if not customer or not products.exists():
        print("缺少测试数据")
        return
    
    try:
        recommender = LoanHistoryRecommender()
        scores = recommender.recommend(customer, products, customer_loans)
        
        print(f"贷款历史推荐分数: {scores}")
        
        # 显示前3个最高分的产品
        product_scores = list(zip(products, scores))
        product_scores.sort(key=lambda x: x[1], reverse=True)
        
        print("\n前3个推荐产品:")
        for i, (product, score) in enumerate(product_scores[:3], 1):
            print(f"{i}. {product.product_name}: {score:.4f}")
            
    except Exception as e:
        print(f"贷款历史推荐器测试失败: {str(e)}")

if __name__ == "__main__":
    test_recommendation_system()
    test_loan_history_recommender() 