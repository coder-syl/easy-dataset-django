#!/usr/bin/env python
"""
推荐系统测试脚本
用于验证推荐系统是否正常工作
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
from application.recommendation.recommender import ProductRecommender

def test_recommendation_system():
    """测试推荐系统"""
    print("开始测试推荐系统...")
    
    try:
        # 1. 检查是否有客户数据
        customers = Customer.objects.all()
        print(f"找到 {customers.count()} 个客户")
        
        if customers.count() == 0:
            print("没有客户数据，创建测试客户...")
            # 创建测试客户
            customer = Customer.objects.create(
                name="测试客户",
                age=30,
                monthly_income=10000,
                yearly_income=120000,
                occupation="工程师",
                company_type="科技公司",
                economic_stability="稳定",
                customer_classification="优质客户",
                total_assets=500000,
                address="北京市朝阳区"
            )
            print(f"创建测试客户: {customer.name}")
        else:
            customer = customers.first()
            print(f"使用现有客户: {customer.name}")
        
        # 2. 检查是否有产品数据
        products = Product.objects.all()
        print(f"找到 {products.count()} 个产品")
        
        if products.count() == 0:
            print("没有产品数据，创建测试产品...")
            # 创建测试产品
            product1 = Product.objects.create(
                product_name="个人信用贷款",
                product_type="信用贷款",
                product_description="低风险个人信用贷款产品",
                min_amount=10000,
                max_amount=500000,
                min_term_months=12,
                max_term_months=60,
                min_interest_rate=0.05,
                max_interest_rate=0.12,
                min_age=18,
                max_age=65,
                risk_level="low",
                online_application=True,
                online_approval=True,
                online_disbursement=True,
                online_repayment=True
            )
            
            product2 = Product.objects.create(
                product_name="消费贷款",
                product_type="消费贷款",
                product_description="中风险消费贷款产品",
                min_amount=5000,
                max_amount=200000,
                min_term_months=6,
                max_term_months=36,
                min_interest_rate=0.08,
                max_interest_rate=0.15,
                min_age=18,
                max_age=60,
                risk_level="medium",
                online_application=True,
                online_approval=True,
                online_disbursement=False,
                online_repayment=True
            )
            
            product3 = Product.objects.create(
                product_name="创业贷款",
                product_type="创业贷款",
                product_description="高风险创业贷款产品",
                min_amount=50000,
                max_amount=1000000,
                min_term_months=24,
                max_term_months=120,
                min_interest_rate=0.10,
                max_interest_rate=0.20,
                min_age=25,
                max_age=55,
                risk_level="high",
                online_application=False,
                online_approval=False,
                online_disbursement=False,
                online_repayment=True
            )
            print("创建了3个测试产品")
        else:
            print("使用现有产品数据")
        
        # 3. 测试推荐系统
        print("\n开始测试推荐系统...")
        recommender = ProductRecommender()
        
        # 获取客户相关数据
        try:
            customer_risk_profile = CustomerRiskProfile.objects.get(customer=customer)
            print(f"找到客户风险画像: {customer_risk_profile.risk_level}")
        except CustomerRiskProfile.MultipleObjectsReturned:
            customer_risk_profile = CustomerRiskProfile.objects.filter(customer=customer).first()
            print(f"找到多条风险画像，默认取第一条: {customer_risk_profile.risk_level}")
        except CustomerRiskProfile.DoesNotExist:
            customer_risk_profile = None
            print("没有找到客户风险画像")
        
        # 获取客户偏好 - 暂时注释掉
        # try:
        #     customer_preferences = CustomerPreference.objects.get(customer=customer)
        #     print(f"客户偏好: 期限{customer_preferences.preferred_term_months}月, 金额{customer_preferences.preferred_amount}")
        # except CustomerPreference.DoesNotExist:
        #     customer_preferences = None
        #     print("客户没有设置偏好")
        
        customer_preferences = None  # 暂时设为None
        
        # 执行推荐
        products = Product.objects.all()
        recommendation_result = recommender.recommend_products(
            customer=customer,
            products=products,
            customer_risk_profile=customer_risk_profile,
            customer_preferences=customer_preferences,
            top_n=3
        )
        
        # 输出结果
        print(f"\n推荐结果状态: {recommendation_result.get('status')}")
        
        if recommendation_result.get('status') == 'success':
            recommendations = recommendation_result.get('recommendations', [])
            print(f"推荐了 {len(recommendations)} 个产品:")
            
            for i, rec in enumerate(recommendations, 1):
                product = rec['product']
                print(f"\n{i}. {product['product_name']}")
                print(f"   匹配度: {rec['score']:.2%}")
                print(f"   产品类型: {product['product_type']}")
                print(f"   风险等级: {product['risk_level']}")
                print(f"   推荐理由: {rec['reason']}")
                print(f"   金额范围: {product['min_amount']}~{product['max_amount']}")
                print(f"   期限范围: {product['min_term_months']}~{product['max_term_months']}个月")
                print(f"   利率范围: {product['min_interest_rate']:.1%}~{product['max_interest_rate']:.1%}")
            
            # 输出统计信息
            statistics = recommendation_result.get('statistics', {})
            if statistics:
                print(f"\n推荐统计:")
                print(f"  总推荐数: {statistics.get('total_recommendations', 0)}")
                print(f"  平均匹配度: {statistics.get('average_score', 0):.2%}")
                print(f"  最高匹配度: {statistics.get('max_score', 0):.2%}")
                print(f"  最低匹配度: {statistics.get('min_score', 0):.2%}")
                print(f"  产品类型分布: {statistics.get('product_type_distribution', {})}")
                print(f"  线上服务比例: {statistics.get('online_service_ratio', 0):.1%}")
        else:
            print(f"推荐失败: {recommendation_result.get('reason', '未知错误')}")
        
        print("\n推荐系统测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_recommendation_system() 