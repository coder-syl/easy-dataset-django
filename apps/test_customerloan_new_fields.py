#!/usr/bin/env python
"""
测试新的CustomerLoan字段
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

from application.models.business import Customer, CustomerLoan

def test_customerloan_new_fields():
    """测试新的CustomerLoan字段"""
    print("=== 测试新的CustomerLoan字段 ===")
    
    # 创建测试客户
    customer, created = Customer.objects.get_or_create(
        name="包义亮",
        defaults={
            'age': 50,
            'gender': '男',
            'occupation': '农民',
            'monthly_income': 5000,
        }
    )
    
    if created:
        print(f"创建新客户: {customer.name}")
    else:
        print(f"找到现有客户: {customer.name}")
    
    # 创建测试贷款记录
    loan_data = {
        'customer_name': '包义亮',
        'cert_id': '320821197309154713',
        'loan_amount': 20000,
        'balance': 0,
        'loan_date': date(2016, 8, 8),
        'expir_date': date(2017, 8, 5),
        'total_prd': 1,
        'clear_date': date(2017, 8, 4),
        'leading_rate': 4.35,
        'repayment_method': '利随本清',
        'interest_collection_cycle': 1,
        'business_type': '短期农户扶贫贴息贷款',
        'loan_status': '结清',
        'product_name': '扶贫贷款',
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }
    
    loan, created = CustomerLoan.objects.get_or_create(
        cert_id=loan_data['cert_id'],
        loan_date=loan_data['loan_date'],
        defaults=loan_data
    )
    
    if created:
        print(f"创建新贷款记录: {loan.customer_name} - {loan.product_name}")
    else:
        print(f"找到现有贷款记录: {loan.customer_name} - {loan.product_name}")
    
    # 显示贷款信息
    print(f"\n贷款详情:")
    print(f"客户姓名: {loan.customer_name}")
    print(f"身份证号: {loan.cert_id}")
    print(f"贷款金额: {loan.loan_amount}")
    print(f"余额: {loan.balance}")
    print(f"贷款日期: {loan.loan_date}")
    print(f"到期日期: {loan.expir_date}")
    print(f"总期数: {loan.total_prd}")
    print(f"结清日期: {loan.clear_date}")
    print(f"利率: {loan.leading_rate}%")
    print(f"还款方式: {loan.repayment_method}")
    print(f"收息周期: {loan.interest_collection_cycle}")
    print(f"业务类型: {loan.business_type}")
    print(f"贷款状态: {loan.loan_status}")
    print(f"产品名称: {loan.product_name}")
    
    # 查询所有贷款记录
    all_loans = CustomerLoan.objects.all()
    print(f"\n总贷款记录数: {all_loans.count()}")
    
    for i, loan in enumerate(all_loans, 1):
        print(f"\n贷款记录 {i}:")
        print(f"  - 客户: {loan.customer_name}")
        print(f"  - 产品: {loan.product_name}")
        print(f"  - 金额: {loan.loan_amount}")
        print(f"  - 状态: {loan.loan_status}")

if __name__ == "__main__":
    test_customerloan_new_fields() 