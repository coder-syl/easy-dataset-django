from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100, null=True)  # 客户名称
    customer_type = models.CharField(max_length=20, null=True)  # 客户类型（个人/公司）
    age = models.IntegerField(null=True)  # 客户年龄
    cert_id = models.CharField(max_length=18, null=True)  # 证件号码
    birth_date = models.DateField(null=True)  # 出生日期
    gender = models.CharField(max_length=10, null=True)  # 客户性别
    is_trusted = models.BooleanField(null=True)  # 是否信用户
    is_dormant = models.BooleanField(null=True)  # 是否睡眠户
    marital_status = models.CharField(max_length=20, null=True)  # 婚姻状态
    education_level = models.CharField(max_length=50, null=True)  # 最高学历
    degree = models.CharField(max_length=50, null=True)  # 学位
    political_status = models.CharField(max_length=50, null=True)  # 政治面貌
    health_status = models.CharField(max_length=50, null=True)  # 健康状况
    occupation_type = models.CharField(max_length=100, null=True)  # 工作类型
    employer_name = models.CharField(max_length=100, null=True)  # 工作单位
    annual_income = models.DecimalField(max_digits=20, decimal_places=2, null=True)  # 年收入
    working_years = models.DecimalField(max_digits=5, decimal_places=2, null=True)  # 工作年限
    main_income_source = models.TextField(null=True)  # 主要收入来源
    business_model = models.CharField(max_length=50, null=True)  # 经营模式
    business_category = models.CharField(max_length=50, null=True)  # 经营主体类别
    business_address = models.CharField(max_length=200, null=True)  # 经营地址
    main_business = models.CharField(max_length=100, null=True)  # 主营业务
    operation_years = models.IntegerField(null=True)  # 经营年限
    rural_entity_type = models.CharField(max_length=100, null=True)  # 新型农村经营主体
    company_name = models.CharField(max_length=100, null=True)  # 公司
    dependents_count = models.IntegerField(null=True)  # 供养人数
    family_income_source = models.TextField(null=True)  # 家庭主要收入来源
    family_annual_income = models.DecimalField(max_digits=20, decimal_places=2, null=True)  # 家庭年收入
    family_annual_expense = models.DecimalField(max_digits=20, decimal_places=2, null=True)  # 家庭年支出
    family_monthly_income = models.DecimalField(max_digits=20, decimal_places=2, null=True)  # 家庭月收入
    family_assets = models.DecimalField(max_digits=24, decimal_places=6, null=True)  # 家庭总资产
    family_debt = models.DecimalField(max_digits=24, decimal_places=6, null=True)  # 家庭总负债
    family_net_assets = models.DecimalField(max_digits=24, decimal_places=6, null=True)  # 家庭净资产
    household_address = models.CharField(max_length=200, null=True)  # 户籍地址
    risk_level = models.CharField(max_length=20, null=True)  # 风险等级
    residence_type = models.CharField(max_length=50, null=True)  # 房产类型
    credit_card = models.JSONField(null=True, blank=True)  # 信用卡信息
    zhengxin = models.JSONField(null=True, blank=True)  # 征信信息
    created_at = models.DateTimeField(null=True)  # 创建时间
    updated_at = models.DateTimeField(null=True)  # 更新时间

class CustomerLoan(models.Model):
    customer_name = models.CharField(max_length=100, null=True)  # 客户姓名
    cert_id = models.CharField(max_length=18, null=True)  # 身份证号
    loan_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)  # 贷款金额
    balance = models.DecimalField(max_digits=20, decimal_places=2, null=True)  # 余额
    loan_date = models.DateField(null=True)  # 贷款日期
    expir_date = models.DateField(null=True)  # 到期日期
    total_prd = models.IntegerField(null=True)  # 总期数
    clear_date = models.DateField(null=True)  # 结清日期
    leading_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True)  # 利率
    repayment_method = models.CharField(max_length=100, null=True)  # 还款方式
    interest_collection_cycle = models.IntegerField(null=True)  # 收息周期
    business_type = models.CharField(max_length=200, null=True)  # 业务类型
    loan_status = models.CharField(max_length=50, null=True)  # 贷款状态
    product_name = models.CharField(max_length=200, null=True)  # 产品名称
    created_at = models.DateTimeField(null=True)  # 创建时间
    updated_at = models.DateTimeField(null=True)  # 更新时间

# class CustomerPreference(models.Model):
#     customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
#     preferred_term_months = models.IntegerField(null=True)
#     preferred_amount = models.FloatField(null=True)
#     risk_tolerance = models.CharField(max_length=20, null=True)
#     online_preference = models.BooleanField(null=True)
#     created_at = models.DateTimeField(null=True)
#     updated_at = models.DateTimeField(null=True)

class CustomerRiskProfile(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    credit_score = models.FloatField(null=True)
    risk_level = models.CharField(max_length=20, null=True)
    default_history = models.BooleanField(null=True)
    debt_ratio = models.FloatField(null=True)
    payment_capability = models.FloatField(null=True)
    credit_rating = models.CharField(max_length=20, null=True)
    credit_record = models.CharField(max_length=50, null=True)
    personal_credit_record = models.CharField(max_length=50, null=True)
    default_times = models.IntegerField(null=True)
    has_loan_history = models.BooleanField(null=True)
    risk_preference = models.CharField(max_length=50, null=True)
    warning_level = models.CharField(max_length=20, null=True)
    external_guarantee_amount = models.DecimalField(max_digits=24, decimal_places=6, null=True)
    bank_relationship = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)

class Product(models.Model):
    product_name = models.CharField(max_length=100, null=True)
    product_type = models.CharField(max_length=50, null=True)
    product_description = models.TextField(null=True)
    min_amount = models.FloatField(null=True)
    max_amount = models.FloatField(null=True)
    min_term_months = models.IntegerField(null=True)
    max_term_months = models.IntegerField(null=True)
    min_interest_rate = models.FloatField(null=True)
    max_interest_rate = models.FloatField(null=True)
    min_age = models.IntegerField(null=True)
    max_age = models.IntegerField(null=True)
    risk_level = models.CharField(max_length=20, null=True)
    target_customers = models.CharField(max_length=500, null=True)
    service_region = models.CharField(max_length=200, null=True)
    online_application = models.BooleanField(null=True)
    online_approval = models.BooleanField(null=True)
    online_disbursement = models.BooleanField(null=True)
    online_repayment = models.BooleanField(null=True)
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)

# class InteractionHistory(models.Model):
#     customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)  # 客户，外键关联Customer表
#     product_id = models.IntegerField(null=True)  # 产品ID
#     interaction_type = models.CharField(max_length=20, null=True)  # 交互类型
#     interaction_time = models.DateTimeField(null=True)  # 交互时间
#     created_at = models.DateTimeField(null=True)  # 创建时间