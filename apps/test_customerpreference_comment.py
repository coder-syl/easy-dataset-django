#!/usr/bin/env python3
"""
测试CustomerPreference注释后的系统功能
"""
import os
import sys
import django

# 设置Django环境
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

def test_imports():
    """测试相关模块导入是否正常"""
    try:
        print("测试导入模块...")
        
        # 测试models导入
        from application.models.business import Customer, Product, CustomerRiskProfile, CustomerLoan, InteractionHistory
        print("✓ models.business导入成功")
        
        # 测试推荐系统导入
        from application.recommendation.recommender import ProductRecommender
        print("✓ recommender导入成功")
        
        # 测试工作流推荐导入
        from application.flow.step_node.recommend_node.impl.recommend import Recommend
        print("✓ recommend node导入成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 导入失败: {str(e)}")
        return False

def test_recommendation():
    """测试推荐系统是否正常工作"""
    try:
        print("\n测试推荐系统...")
        
        # 创建推荐器实例
        recommender = ProductRecommender()
        print("✓ ProductRecommender创建成功")
        
        # 获取测试数据
        customers = Customer.objects.all()
        products = Product.objects.all()
        
        if customers.exists() and products.exists():
            customer = customers.first()
            product_list = list(products[:3])
            
            print(f"✓ 找到测试客户: {customer.name}")
            print(f"✓ 找到测试产品: {len(product_list)}个")
            
            # 测试推荐功能
            result = recommender.recommend_products(
                customer=customer,
                products=product_list,
                customer_preferences=None,  # 现在传入None
                top_n=3
            )
            
            print(f"✓ 推荐系统运行成功，返回状态: {result.get('status', 'unknown')}")
            
            if result.get('recommendations'):
                print(f"✓ 生成推荐: {len(result['recommendations'])}个")
            
        else:
            print("! 没有找到测试数据，跳过推荐测试")
            
        return True
        
    except Exception as e:
        print(f"✗ 推荐系统测试失败: {str(e)}")
        return False

def test_workflow_recommend():
    """测试工作流推荐节点"""
    try:
        print("\n测试工作流推荐...")
        
        # 创建推荐节点实例
        recommend_node = Recommend()
        print("✓ Recommend节点创建成功")
        
        # 测试获取推荐
        customers = Customer.objects.all()
        if customers.exists():
            customer = customers.first()
            recommendations = recommend_node.get_recommendations(customer.id, top_n=3)
            
            print(f"✓ 工作流推荐运行成功，返回推荐数: {len(recommendations)}")
            
            # 测试获取客户信息
            user_info = recommend_node.get_customer_info(customer.id)
            if user_info:
                print("✓ 获取客户信息成功")
                print(f"  客户姓名: {user_info.get('name', 'N/A')}")
                print(f"  偏好设置: {user_info.get('preference', 'None')}")
            
        else:
            print("! 没有找到测试数据，跳过工作流测试")
            
        return True
        
    except Exception as e:
        print(f"✗ 工作流推荐测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("CustomerPreference注释测试")
    print("=" * 60)
    
    # 运行测试
    tests = [
        ("导入测试", test_imports),
        ("推荐系统测试", test_recommendation),
        ("工作流推荐测试", test_workflow_recommend)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        try:
            passed = test_func()
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"✗ {test_name}异常: {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！CustomerPreference注释成功，系统功能正常。")
    else:
        print("❌ 部分测试失败，请检查代码。")
    print("=" * 60)

if __name__ == "__main__":
    main() 