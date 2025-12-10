#!/usr/bin/env python
"""
第三方客户信息获取使用示例 - 不需要配置文件
"""

import os
import sys
import django

# 设置Django环境
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartdoc.settings")
django.setup()

from application.services.third_party_customer import get_customer_from_third_party, create_customer_from_third_party, ThirdPartyCustomerClient


def example_usage():
    """第三方客户信息获取使用示例"""
    print("=== 第三方客户信息获取使用示例 ===")
    
    # 第三方API配置
    api_url = "http://your-third-party-api.com/api/v1"  # 替换为实际的API地址
    api_key = "your-api-key"  # 替换为实际的API密钥
    
    # 方法一：直接使用便捷方法
    print("\n1. 使用便捷方法获取客户信息:")
    
    # 根据客户ID获取
    customer_data = get_customer_from_third_party(
        customer_id="12345",
        api_url=api_url,
        api_key=api_key
    )
    
    if customer_data:
        print(f"   客户姓名: {customer_data.get('name')}")
        print(f"   客户年龄: {customer_data.get('age')}")
        print(f"   月收入: {customer_data.get('monthly_income')}")
        print(f"   数据源: {customer_data.get('data_source')}")
    else:
        print("   未找到客户信息")
    
    # 根据手机号获取
    customer_data = get_customer_from_third_party(
        phone="13800138000",
        api_url=api_url,
        api_key=api_key
    )
    
    if customer_data:
        print(f"   手机号客户: {customer_data.get('name')}")
    else:
        print("   未找到手机号对应的客户")
    
    # 方法二：使用客户端类
    print("\n2. 使用客户端类:")
    
    client = ThirdPartyCustomerClient(
        api_url=api_url,
        api_key=api_key,
        timeout=30  # 自定义超时时间
    )
    
    customer_data = client.get_customer_info(customer_id="12345")
    
    if customer_data:
        print(f"   客户信息: {customer_data.get('name')}")
        print(f"   职业: {customer_data.get('occupation')}")
        print(f"   地址: {customer_data.get('address')}")
    else:
        print("   获取客户信息失败")
    
    # 方法三：直接创建Customer对象
    print("\n3. 创建Customer对象:")
    
    customer_obj = create_customer_from_third_party(
        customer_id="12345",
        api_url=api_url,
        api_key=api_key
    )
    
    if customer_obj:
        print(f"   创建成功，客户ID: {customer_obj.id}")
        print(f"   客户姓名: {customer_obj.name}")
        print(f"   客户年龄: {customer_obj.age}")
    else:
        print("   创建客户对象失败")


def minimal_example():
    """最简单的使用示例"""
    print("\n=== 最简单的使用示例 ===")
    
    # 最简单的用法：使用默认配置
    customer_data = get_customer_from_third_party(
        customer_id="12345",
        api_url="http://your-api.com/api/v1",
        api_key="your-key"
    )
    
    if customer_data:
        print("成功获取客户信息！")
        print(f"客户姓名: {customer_data.get('name', '未知')}")
        print(f"客户年龄: {customer_data.get('age', '未知')}")
    else:
        print("获取客户信息失败")


if __name__ == "__main__":
    # 运行示例
    example_usage()
    minimal_example()
    
    print("\n=== 使用说明 ===")
    print("1. 将 api_url 和 api_key 替换为实际的第三方API地址和密钥")
    print("2. 根据需要调整参数，如超时时间等")
    print("3. 可以根据customer_id、phone或id_card查询客户信息")
    print("4. 支持直接获取字典数据或创建Customer对象")
    print("5. 内置缓存机制，相同查询1小时内不会重复请求API") 