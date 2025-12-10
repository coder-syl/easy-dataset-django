"""
Enhanced Compliance Rules Engine for financial product recommendation system.
"""
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
from datetime import datetime
import logging
import json
from dataclasses import dataclass

class RuleType(Enum):
    """规则类型枚举"""
    PRODUCT_ELIGIBILITY = "product_eligibility"     # 产品准入规则
    CUSTOMER_QUALIFICATION = "customer_qualification" # 客户资质规则
    RISK_CONTROL = "risk_control"                   # 风险控制规则
    MARKETING_COMPLIANCE = "marketing_compliance"    # 营销合规规则
    REGULATORY_REQUIREMENT = "regulatory_requirement" # 监管要求规则
    BUSINESS_LOGIC = "business_logic"               # 业务逻辑规则

class RuleSeverity(Enum):
    """规则严重程度枚举"""
    CRITICAL = "critical"  # 严重：必须阻止操作
    HIGH = "high"         # 高：建议阻止操作
    MEDIUM = "medium"     # 中：需要警告
    LOW = "low"          # 低：仅提示

@dataclass
class RuleContext:
    """规则上下文数据类"""
    customer: Dict[str, Any]
    risk_profile: Optional[Dict[str, Any]] = None
    product: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    additional_params: Optional[Dict[str, Any]] = None

class ComplianceRule:
    """合规规则类"""
    def __init__(self,
                 rule_id: str,
                 rule_type: RuleType,
                 severity: RuleSeverity,
                 description: str,
                 validation_func: Callable[[RuleContext], Tuple[bool, str]],
                 error_message: str = None,
                 enabled: bool = True):
        self.rule_id = rule_id
        self.rule_type = rule_type
        self.severity = severity
        self.description = description
        self.validation_func = validation_func
        self.error_message = error_message or description
        self.enabled = enabled
        self.created_at = datetime.now()
        self.last_updated = datetime.now()

    def validate(self, context: RuleContext) -> Tuple[bool, str]:
        """
        执行规则验证
        :return: (是否通过, 消息)
        """
        if not self.enabled:
            return True, "Rule is disabled"
        return self.validation_func(context)

class ComplianceRulesEngine:
    """合规规则引擎"""
    def __init__(self):
        self.rules: Dict[str, ComplianceRule] = {}
        self.logger = logging.getLogger(__name__)
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """初始化默认规则集"""
        # 1. 客户资质规则
        self._add_customer_qualification_rules()
        # 2. 产品准入规则
        self._add_product_eligibility_rules()
        # 3. 风险控制规则
        self._add_risk_control_rules()
        # 4. 营销合规规则
        self._add_marketing_compliance_rules()

    def _add_customer_qualification_rules(self):
        """添加客户资质相关规则"""
        # 年龄规则
        self.add_rule(
            rule_id="CUST_AGE_001",
            rule_type=RuleType.CUSTOMER_QUALIFICATION,
            severity=RuleSeverity.CRITICAL,
            description="客户年龄必须在18-65岁之间",
            validation_func=self._validate_customer_age
        )

        # 收入规则
        self.add_rule(
            rule_id="CUST_INCOME_001",
            rule_type=RuleType.CUSTOMER_QUALIFICATION,
            severity=RuleSeverity.HIGH,
            description="客户月收入必须达到最低要求",
            validation_func=self._validate_customer_income
        )

        # # 信用记录规则
        # self.add_rule(
        #     rule_id="CUST_CREDIT_001",
        #     rule_type=RuleType.CUSTOMER_QUALIFICATION,
        #     severity=RuleSeverity.HIGH,
        #     description="客户信用记录必须符合要求",
        #     validation_func=self._validate_customer_credit
        # )

    def _add_product_eligibility_rules(self):
        """添加产品准入相关规则"""
        # 产品匹配度规则
        self.add_rule(
            rule_id="PROD_MATCH_001",
            rule_type=RuleType.PRODUCT_ELIGIBILITY,
            severity=RuleSeverity.HIGH,
            description="产品必须与客户风险等级匹配",
            validation_func=self._validate_product_risk_match
        )

        # 产品额度规则
        self.add_rule(
            rule_id="PROD_LIMIT_001",
            rule_type=RuleType.PRODUCT_ELIGIBILITY,
            severity=RuleSeverity.CRITICAL,
            description="贷款额度必须在客户可承受范围内",
            validation_func=self._validate_loan_limit
        )

    def _add_risk_control_rules(self):
        """添加风险控制相关规则"""
        # 多头借贷规则
        self.add_rule(
            rule_id="RISK_MULTI_LOAN_001",
            rule_type=RuleType.RISK_CONTROL,
            severity=RuleSeverity.HIGH,
            description="检查是否存在多头借贷风险",
            validation_func=self._validate_multiple_loans
        )

    def _add_marketing_compliance_rules(self):
        """添加营销合规相关规则"""
        # 营销话术合规规则
        self.add_rule(
            rule_id="MKT_CONTENT_001",
            rule_type=RuleType.MARKETING_COMPLIANCE,
            severity=RuleSeverity.HIGH,
            description="营销内容必须符合合规要求",
            validation_func=self._validate_marketing_content
        )

    def add_rule(self, rule_id: str, rule_type: RuleType,
                severity: RuleSeverity, description: str,
                validation_func: Callable[[RuleContext], Tuple[bool, str]],
                error_message: str = None,
                enabled: bool = True) -> None:
        """添加新规则"""
        self.rules[rule_id] = ComplianceRule(
            rule_id=rule_id,
            rule_type=rule_type,
            severity=severity,
            description=description,
            validation_func=validation_func,
            error_message=error_message,
            enabled=enabled
        )

    def validate(self, context: Dict[str, Any], rule_types: Optional[List[RuleType]] = None) -> List[Dict[str, Any]]:
        """
        执行规则验证
        :param context: 验证上下文
        :param rule_types: 可选的规则类型列表，如果指定则只验证这些类型的规则
        :return: 验证结果列表
        """
        rule_context = RuleContext(**context)
        results = []

        try:
            for rule in self.rules.values():
                # 如果指定了规则类型且当前规则不在其中，则跳过
                if rule_types and rule.rule_type not in rule_types:
                    continue

                try:
                    is_valid, message = rule.validate(rule_context)
                    results.append({
                        'rule_id': rule.rule_id,
                        'rule_type': rule.rule_type.value,
                        'severity': rule.severity.value,
                        'is_valid': is_valid,
                        'message': message
                    })

                    # 对于严重违规，记录警告日志
                    if not is_valid and rule.severity in [RuleSeverity.CRITICAL, RuleSeverity.HIGH]:
                        self.logger.warning(
                            f"Compliance violation: {rule.rule_id} - {message}")

                except Exception as e:
                    self.logger.error(
                        f"Error validating rule {rule.rule_id}: {str(e)}")
                    results.append({
                        'rule_id': rule.rule_id,
                        'rule_type': rule.rule_type.value,
                        'severity': rule.severity.value,
                        'is_valid': False,
                        'message': f"验证错误: {str(e)}"
                    })

        except Exception as e:
            self.logger.error(f"Error during compliance validation: {str(e)}")
            results.append({
                'rule_id': 'SYSTEM_ERROR',
                'rule_type': 'system',
                'severity': RuleSeverity.CRITICAL.value,
                'is_valid': False,
                'message': f"系统错误: {str(e)}"
            })

        return results

    def _validate_customer_age(self, context: RuleContext) -> Tuple[bool, str]:
        """验证客户年龄"""
        age = context.customer.get('age', 0)
        if not isinstance(age, (int, float)):
            return False, "年龄数据类型错误"
        if not (18 <= age <= 65):
            return False, f"客户年龄 {age} 不在产品准入范围(18-65)内"
        return True, "年龄验证通过"

    def _validate_customer_income(self, context: RuleContext) -> Tuple[bool, str]:
        """验证客户收入"""
        # 获取年收入并转换为月收入
        annual_income = context.customer.get('income', 0)
        if not isinstance(annual_income, (int, float)):
            return False, "收入数据类型错误"
        
        monthly_income = annual_income / 12
        if monthly_income < 3000:
            return False, f"月收入{monthly_income:.2f}低于最低要求(3000)"
        return True, "收入验证通过"

    def _validate_customer_credit(self, context: RuleContext) -> Tuple[bool, str]:
        """验证客户信用"""
        credit_score = context.customer.get('credit_score')
        if credit_score is None:
            return False, "未提供信用分数据"
        if not isinstance(credit_score, (int, float)):
            return False, "信用分数据类型错误"
        if credit_score < 600:
            return False, f"信用分{credit_score}低于最低要求(600)"
        return True, "信用验证通过"

    def _validate_product_risk_match(self, context: RuleContext) -> Tuple[bool, str]:
        """验证产品风险匹配度"""
        if not context.product:
            return False, "缺少产品信息"
        
        user_risk_level = context.customer.get('risk_level', 'medium')
        product_risk_level = context.product.get('risk_level', 'medium')
        
        risk_levels = {'low': 1, 'medium': 2, 'high': 3}
        if risk_levels.get(product_risk_level, 0) > risk_levels.get(user_risk_level, 0):
            return False, f"产品风险等级({product_risk_level})高于客户承受能力({user_risk_level})"
        return True, "风险等级匹配验证通过"

    def _validate_loan_limit(self, context: RuleContext) -> Tuple[bool, str]:
        """验证贷款额度"""
        if not context.product:
            return False, "缺少产品信息"
            
        monthly_income = context.customer.get('monthly_income', 0)
        loan_amount = context.product.get('loan_amount', 0)
        
        # 假设月供不能超过月收入的50%
        max_monthly_payment = monthly_income * 0.5
        estimated_monthly_payment = self._calculate_monthly_payment(loan_amount)
        
        if estimated_monthly_payment > max_monthly_payment:
            return False, f"月供({estimated_monthly_payment:.2f})超过可承受范围({max_monthly_payment:.2f})，超过月收入50%"
        return True, "贷款额度验证通过"

    def _validate_multiple_loans(self, context: RuleContext) -> Tuple[bool, str]:
        """验证多头借贷风险"""
        loan_count = context.customer.get('existing_loans', 0)
        if loan_count >= 3:
            return False, f"已有{loan_count}笔贷款，不建议继续借贷"
        return True, "多头借贷检查通过"

    def _validate_marketing_content(self, context: RuleContext) -> Tuple[bool, str]:
        """验证营销内容合规性"""
        content = context.additional_params.get('marketing_content', '')
        forbidden_words = [
            "保证", "承诺", "100%", "最高", "最低",
            "无风险", "零风险", "稳赚", "保本",
            "高收益", "快速审批", "秒批", "秒放"
        ]
        
        found_words = [word for word in forbidden_words if word in content]
        if found_words:
            return False, f"营销内容包含禁用词: {', '.join(found_words)}"
        return True, "营销内容验证通过"

    def _calculate_monthly_payment(self, loan_amount: float, 
                                annual_rate: float = 0.1, 
                                years: int = 1) -> float:
        """计算月供"""
        if loan_amount <= 0:
            return 0
        monthly_rate = annual_rate / 12
        num_payments = years * 12
        if monthly_rate == 0:
            return loan_amount / num_payments
        return loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)

    def get_rules_by_type(self, rule_type: RuleType) -> List[ComplianceRule]:
        """获取指定类型的所有规则"""
        return [rule for rule in self.rules.values() if rule.rule_type == rule_type]

    def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        """获取指定ID的规则"""
        return self.rules.get(rule_id)

    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False

    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False

    def remove_rule(self, rule_id: str) -> bool:
        """删除规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False 