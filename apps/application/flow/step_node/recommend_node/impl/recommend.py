# coding=utf-8
"""
推荐服务 - 基于CustMark项目的金融产品推荐系统
直接调用application.recommendation.recommender中的ProductRecommender
避免代码冗余，保持逻辑一致性
"""

import logging
from typing import List, Dict, Any, Optional
from application.models.business import (
    Customer, Product, CustomerLoan, # CustomerPreference,
    CustomerRiskProfile, # InteractionHistory
)
from application.recommendation.recommender import ProductRecommender
from application.services.third_party_customer import get_customer_from_third_party, get_customer_loan_from_third_party

logger = logging.getLogger('max_kb')

class Recommend:
    """
    推荐服务主类
    提供客户产品推荐功能，直接调用ProductRecommender
    """
    
    def __init__(self):
        self.product_recommender = ProductRecommender()
        
    def get_recommendations(self, customer_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        获取客户推荐列表
        
        Args:
            customer_id: 客户ID
            top_n: 推荐产品数量，默认5个
            
        Returns:
            推荐产品列表
        """
        logger.info(f"Getting recommendations for customer_id: {customer_id}, top_n: {top_n}")
        
        try:
            # 1. 获取客户基础信息
            customer = get_customer_from_third_party(customer_id)
            logger.info(f"Found customer: {customer.name}, age: {customer.age}")

            # 2. 获取客户风险画像
            customer_risk_profile = None
            try:
                customer_risk_profile = CustomerRiskProfile.objects.get(customer=customer)
            except CustomerRiskProfile.MultipleObjectsReturned:
                customer_risk_profile = CustomerRiskProfile.objects.filter(customer=customer).first()
            except CustomerRiskProfile.DoesNotExist:
                pass

            # 3. 获取客户偏好 - 暂时注释掉
            # try:
            #     customer_preferences = CustomerPreference.objects.get(customer=customer)
            # except CustomerPreference.DoesNotExist:
            #     customer_preferences = None
            
            customer_preferences = None  # 暂时设为None

            # 4. 获取客户贷款历史
            # customer_loans = CustomerLoan.objects.filter(cert_id=customer.cert_id)
            customer_loans = get_customer_loan_from_third_party(customer.cert_id)

            # 5. 获取交互历史
            # interaction_history = InteractionHistory.objects.filter(customer=customer)

            # 6. 获取所有产品
            products = Product.objects.all()
            if not products:
                logger.warning("No products available for recommendation")
                return []

            logger.info(f"Found {len(products)} available products")

            # 7. 使用推荐系统
            recommendation_result = self.product_recommender.recommend_products(
                customer=customer,
                products=products,
                customer_risk_profile=customer_risk_profile,
                customer_preferences=customer_preferences,
                # interaction_history=list(interaction_history),
                customer_loans=list(customer_loans),
                top_n=top_n
            )

            # 8. 处理推荐结果
            recommend_list = []
            if recommendation_result.get("status") == "success":
                recommendations = recommendation_result.get("recommendations", [])
                for rec in recommendations:
                    product = rec["product"]
                    recommend_list.append({
                        "name": product["product_name"],
                        "match": int(rec["score"] * 100),  # 转换为百分比
                        "desc": product["product_description"] or "-",
                        "amount": f"{product['min_amount']}~{product['max_amount']}" if product['min_amount'] and product['max_amount'] else "-",
                        "term": f"{product['min_term_months']}~{product['max_term_months']}" if product['min_term_months'] and product['max_term_months'] else "-",
                        "rate": f"{product['min_interest_rate']}~{product['max_interest_rate']}" if product['min_interest_rate'] and product['max_interest_rate'] else "-",
                        "reason": rec["reason"],
                        "productType": product["product_type"],
                        "riskLevel": product["risk_level"],
                        "onlineService": product["online_application"] and product["online_approval"],
                        "productId": product["id"],
                        # 工作流兼容字段
                        "id": product["id"],
                        "type": product["product_type"],
                        "description": product["product_description"],
                        "min_amount": self._safe_float(product.get('min_amount')),
                        "max_amount": self._safe_float(product.get('max_amount')),
                        "min_term_months": product.get('min_term_months'),
                        "max_term_months": product.get('max_term_months'),
                        "min_interest_rate": self._safe_float(product.get('min_interest_rate')),
                        "max_interest_rate": self._safe_float(product.get('max_interest_rate')),
                        "risk_level": product.get('risk_level'),
                        "online_application": product.get('online_application', False),
                        "online_approval": product.get('online_approval', False),
                        "online_disbursement": product.get('online_disbursement', False),
                        "online_repayment": product.get('online_repayment', False),
                        "score": rec.get('score', 0.0),
                        "match_percentage": int(rec.get('score', 0.0) * 100)
                    })
                logger.info(f"Successfully generated {len(recommend_list)} recommendations")
            else:
                # 如果推荐失败，使用默认推荐
                logger.warning(f"Recommendation failed: {recommendation_result.get('reason', 'Unknown error')}, using default recommendations")
                products_default = Product.objects.all()[:top_n]
                for p in products_default:
                    recommend_list.append({
                        "name": p.product_name,
                        "match": 60,
                        "desc": p.product_description or "-",
                        "amount": f"{p.min_amount}~{p.max_amount}" if p.min_amount and p.max_amount else "-",
                        "term": f"{p.min_term_months}~{p.max_term_months}" if p.min_term_months and p.max_term_months else "-",
                        "rate": f"{p.min_interest_rate}~{p.max_interest_rate}" if p.min_interest_rate and p.max_interest_rate else "-",
                        "reason": "基于基础规则匹配",
                        "productType": p.product_type,
                        "riskLevel": p.risk_level,
                        "onlineService": p.online_application and p.online_approval,
                        "productId": p.id,
                        # 工作流兼容字段
                        "id": p.id,
                        "type": p.product_type,
                        "description": p.product_description,
                        "min_amount": self._safe_float(p.min_amount),
                        "max_amount": self._safe_float(p.max_amount),
                        "min_term_months": p.min_term_months,
                        "max_term_months": p.max_term_months,
                        "min_interest_rate": self._safe_float(p.min_interest_rate),
                        "max_interest_rate": self._safe_float(p.max_interest_rate),
                        "risk_level": p.risk_level,
                        "online_application": p.online_application,
                        "online_approval": p.online_approval,
                        "online_disbursement": p.online_disbursement,
                        "online_repayment": p.online_repayment,
                        "score": 0.6,
                        "match_percentage": 60
                    })

            return recommend_list

        except Customer.DoesNotExist:
            logger.error(f"Customer not found with ID: {customer_id}")
            return []
        except Exception as e:
            logger.error(f"Error in get_recommendations: {str(e)}", exc_info=True)
            return []

    def get_customer_info_and_recommendations(self, customer_id: int, top_n: int = 5) -> Dict[str, Any]:
        """
        同时获取客户信息和推荐列表，避免重复查询
        
        Args:
            customer_id: 客户ID
            top_n: 推荐产品数量，默认5个
            
        Returns:
            包含客户信息和推荐列表的字典
        """
        logger.info(f"Getting customer info and recommendations for customer_id: {customer_id}, top_n: {top_n}")
        
        try:
            # 1. 获取客户基础信息
            customer = get_customer_from_third_party(customer_id)
            logger.info(f"Found customer: {customer.name}, age: {customer.age}")

            # 2. 获取客户风险画像
            customer_risk_profile = None
            try:
                customer_risk_profile = CustomerRiskProfile.objects.get(customer=customer)
            except CustomerRiskProfile.MultipleObjectsReturned:
                customer_risk_profile = CustomerRiskProfile.objects.filter(customer=customer).first()
            except CustomerRiskProfile.DoesNotExist:
                pass

            # 3. 获取客户偏好 - 暂时注释掉
            customer_preferences = None  # 暂时设为None

            # 4. 获取客户贷款历史
            customer_loans = get_customer_loan_from_third_party(customer.cert_id)
            logger.info(f"客户贷款历史----------------------\n: {customer_loans}")

            # 5. 获取交互历史
            # interaction_history = InteractionHistory.objects.filter(customer=customer)

            # 6. 获取所有产品
            products = Product.objects.all()
            if not products:
                logger.warning("No products available for recommendation")
                return {
                    "user_info": self._build_user_info(customer, customer_risk_profile, customer_preferences, customer_loans),
                    "recommend_list": []
                }

            logger.info(f"Found {len(products)} available products")

            # 7. 使用推荐系统
            recommendation_result = self.product_recommender.recommend_products(
                customer=customer,
                products=products,
                customer_risk_profile=customer_risk_profile,
                customer_preferences=customer_preferences,
                # interaction_history=list(interaction_history),
                customer_loans=list(customer_loans),
                top_n=top_n
            )

            # 8. 处理推荐结果
            recommend_list = []
            if recommendation_result.get("status") == "success":
                recommendations = recommendation_result.get("recommendations", [])
                for rec in recommendations:
                    product = rec["product"]
                    recommend_list.append({
                        "name": product["product_name"],
                        "match": int(rec["score"] * 100),  # 转换为百分比
                        "desc": product["product_description"] or "-",
                        "amount": f"{product['min_amount']}~{product['max_amount']}" if product['min_amount'] and product['max_amount'] else "-",
                        "term": f"{product['min_term_months']}~{product['max_term_months']}" if product['min_term_months'] and product['max_term_months'] else "-",
                        "rate": f"{product['min_interest_rate']}~{product['max_interest_rate']}" if product['min_interest_rate'] and product['max_interest_rate'] else "-",
                        "reason": rec["reason"],
                        "productType": product["product_type"],
                        "riskLevel": product["risk_level"],
                        "onlineService": product["online_application"] and product["online_approval"],
                        "productId": product["id"],
                        # 工作流兼容字段
                        "id": product["id"],
                        "type": product["product_type"],
                        "description": product["product_description"],
                        "min_amount": self._safe_float(product.get('min_amount')),
                        "max_amount": self._safe_float(product.get('max_amount')),
                        "min_term_months": product.get('min_term_months'),
                        "max_term_months": product.get('max_term_months'),
                        "min_interest_rate": self._safe_float(product.get('min_interest_rate')),
                        "max_interest_rate": self._safe_float(product.get('max_interest_rate')),
                        "risk_level": product.get('risk_level'),
                        "online_application": product.get('online_application', False),
                        "online_approval": product.get('online_approval', False),
                        "online_disbursement": product.get('online_disbursement', False),
                        "online_repayment": product.get('online_repayment', False),
                        "score": rec.get('score', 0.0),
                        "match_percentage": int(rec.get('score', 0.0) * 100)
                    })
                logger.info(f"Successfully generated {len(recommend_list)} recommendations")
            else:
                # 如果推荐失败，使用默认推荐
                logger.warning(f"Recommendation failed: {recommendation_result.get('reason', 'Unknown error')}, using default recommendations")
                products_default = Product.objects.all()[:top_n]
                for p in products_default:
                    recommend_list.append({
                        "name": p.product_name,
                        "match": 60,
                        "desc": p.product_description or "-",
                        "amount": f"{p.min_amount}~{p.max_amount}" if p.min_amount and p.max_amount else "-",
                        "term": f"{p.min_term_months}~{p.max_term_months}" if p.min_term_months and p.max_term_months else "-",
                        "rate": f"{p.min_interest_rate}~{p.max_interest_rate}" if p.min_interest_rate and p.max_interest_rate else "-",
                        "reason": "基于基础规则匹配",
                        "productType": p.product_type,
                        "riskLevel": p.risk_level,
                        "onlineService": p.online_application and p.online_approval,
                        "productId": p.id,
                        # 工作流兼容字段
                        "id": p.id,
                        "type": p.product_type,
                        "description": p.product_description,
                        "min_amount": self._safe_float(p.min_amount),
                        "max_amount": self._safe_float(p.max_amount),
                        "min_term_months": p.min_term_months,
                        "max_term_months": p.max_term_months,
                        "min_interest_rate": self._safe_float(p.min_interest_rate),
                        "max_interest_rate": self._safe_float(p.max_interest_rate),
                        "risk_level": p.risk_level,
                        "online_application": p.online_application,
                        "online_approval": p.online_approval,
                        "online_disbursement": p.online_disbursement,
                        "online_repayment": p.online_repayment,
                        "score": 0.6,
                        "match_percentage": 60
                    })

            # 9. 构建用户信息
            user_info = self._build_user_info(customer, customer_risk_profile, customer_preferences, customer_loans)

            return {
                "user_info": user_info,
                "recommend_list": recommend_list
            }

        except Customer.DoesNotExist:
            logger.error(f"Customer not found with ID: {customer_id}")
            return {"user_info": None, "recommend_list": []}
        except Exception as e:
            logger.error(f"Error in get_customer_info_and_recommendations: {str(e)}", exc_info=True)
            return {"user_info": None, "recommend_list": []}

    def _build_user_info(self, customer, customer_risk_profile, customer_preferences, customer_loans):
            """构建用户信息字典（新版字段）"""
            try:
                return {
                    # 基本信息
                    "id": customer.id,
                    "name": customer.name,
                    "customer_type": customer.customer_type,
                    "age": customer.age,
                    "cert_id": customer.cert_id,
                    "birth_date": customer.birth_date.isoformat() if customer.birth_date else None,
                    "gender": customer.gender,
                    "is_trusted": customer.is_trusted,
                    "is_dormant": customer.is_dormant,
                    "marital_status": customer.marital_status,
                    "education_level": customer.education_level,
                    "degree": customer.degree,
                    "political_status": customer.political_status,
                    "health_status": customer.health_status,
                    "occupation_type": customer.occupation_type,
                    "employer_name": customer.employer_name,
                    "annual_income": float(customer.annual_income) if customer.annual_income else None,
                    "working_years": float(customer.working_years) if customer.working_years else None,
                    "main_income_source": customer.main_income_source,
                    "business_model": customer.business_model,
                    "business_category": customer.business_category,
                    "business_address": customer.business_address,
                    "main_business": customer.main_business,
                    "operation_years": customer.operation_years,
                    "rural_entity_type": customer.rural_entity_type,
                    "company_name": customer.company_name,
                    "dependents_count": customer.dependents_count,
                    "family_income_source": customer.family_income_source,
                    "family_annual_income": float(customer.family_annual_income) if customer.family_annual_income else None,
                    "family_annual_expense": float(customer.family_annual_expense) if customer.family_annual_expense else None,
                    "family_monthly_income": float(customer.family_monthly_income) if customer.family_monthly_income else None,
                    "family_assets": float(customer.family_assets) if customer.family_assets else None,
                    "family_debt": float(customer.family_debt) if customer.family_debt else None,
                    "family_net_assets": float(customer.family_net_assets) if customer.family_net_assets else None,
                    "household_address": customer.household_address,
                    "risk_level": customer.risk_level,
                    "residence_type": customer.residence_type,
                    "zhengxin": customer.zhengxin,
                    "created_at": customer.created_at.isoformat() if customer.created_at else None,
                    "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,

                    # 风险画像
                    "risk_profile": {
                        "risk_level": customer_risk_profile.risk_level if customer_risk_profile else None,
                        "credit_score": float(customer_risk_profile.credit_score) if customer_risk_profile and customer_risk_profile.credit_score else None,
                        "credit_rating": customer_risk_profile.credit_rating if customer_risk_profile else None,
                        "credit_record": customer_risk_profile.credit_record if customer_risk_profile else None,
                        "default_history": customer_risk_profile.default_history if customer_risk_profile else None,
                        "debt_ratio": float(customer_risk_profile.debt_ratio) if customer_risk_profile and customer_risk_profile.debt_ratio else None,
                        "payment_capability": float(customer_risk_profile.payment_capability) if customer_risk_profile and customer_risk_profile.payment_capability else None,
                        "warning_level": customer_risk_profile.warning_level if customer_risk_profile else None,
                    } if customer_risk_profile else None,

                    # 客户偏好
                    "preference": {
                        "preferred_term_months": customer_preferences.preferred_term_months if customer_preferences else None,
                        "preferred_amount": float(customer_preferences.preferred_amount) if customer_preferences and customer_preferences.preferred_amount else None,
                        "risk_tolerance": customer_preferences.risk_tolerance if customer_preferences else None,
                        "online_preference": customer_preferences.online_preference if customer_preferences else None,
                    } if customer_preferences else None,

                    # 贷款信息
                    "loans": [
                        {
                            "loan_amount": float(loan.loan_amount) if loan.loan_amount else None,
                            "balance": float(loan.balance) if loan.balance else None,
                            "business_type": loan.business_type,
                            "loan_status": loan.loan_status,
                            "leading_rate": float(loan.leading_rate) if loan.leading_rate else None,
                            "loan_date": loan.loan_date.isoformat() if loan.loan_date else None,
                            "expir_date": loan.expir_date.isoformat() if loan.expir_date else None,
                            "product_name": loan.product_name,
                        }
                        for loan in customer_loans
                    ],
                }
            except Exception as e:
                logger.error(f"Error building user info for customer {customer.id}: {str(e)}", exc_info=True)
                # 返回基本信息
                return {
                    "id": customer.id,
                    "name": customer.name,
                    "error": "部分信息获取失败"
                }

    def get_customer_info(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        获取客户基本信息（用于返回给前端）
        参考chat_views.py中的实现
        
        Args:
            customer_id: 客户ID
            
        Returns:
            客户信息字典或None
        """
        try:
            customer = get_customer_from_third_party(customer_id)
            
            # 获取客户风险画像
            customer_risk_profile = None
            try:
                customer_risk_profile = CustomerRiskProfile.objects.get(customer=customer)
            except CustomerRiskProfile.MultipleObjectsReturned:
                customer_risk_profile = CustomerRiskProfile.objects.filter(customer=customer).first()
            except CustomerRiskProfile.DoesNotExist:
                pass
            
            # 获取客户偏好 - 暂时注释掉
            # customer_preferences = None
            # try:
            #     customer_preferences = CustomerPreference.objects.get(customer=customer)
            # except CustomerPreference.DoesNotExist:
            #     pass
            
            customer_preferences = None  # 暂时设为None
            
            # 获取客户贷款历史
            # customer_loans = CustomerLoan.objects.filter(cert_id=customer.cert_id)
            customer_loans = get_customer_loan_from_third_party(customer.cert_id)
            logger.info(f"客户贷款历史----------------------\n: {customer_loans}")
                
            # 构建完整的用户信息，参考chat_views.py的格式
            user_info = {
                # 基本信息
                "id": customer.id,
                "name": customer.name,
                "gender": customer.gender,
                "age": customer.age,
                "marital_status": customer.marital_status,
                "education_level": customer.education_level,
                "address": customer.household_address,
                "region": customer.region,
                "marketing_type": customer.marketing_type,
                
                # 收入信息
                "monthly_income": float(customer.annual_income)/12 if customer.annual_income else None,
                "yearly_income": float(customer.annual_income) if customer.annual_income else None,
                "family_monthly_income": float(customer.family_monthly_income) if customer.family_monthly_income else None,
                "family_yearly_income": float(customer.family_annual_income) if customer.family_annual_income else None,
                "income_source": customer.main_income_source,
                "economic_stability": customer.economic_stability,
                
                # 资产信息
                "total_assets": float(customer.family_assets) if customer.family_assets else None,
                "total_liabilities": float(customer.family_debt) if customer.family_debt else None,
                "net_assets": float(customer.family_net_assets) if customer.family_net_assets else None,
                "house_property": customer.residence_type,
                "zhengxin": customer.zhengxin,
                
                # 职业信息
                "occupation": customer.occupation_type,
                "position": customer.position,
                "company_type": customer.employer_name,
                "industry_type": customer.industry_type,
                "work_start_date": customer.work_start_date.isoformat() if customer.work_start_date else None,
                "is_business_owner": customer.is_business_owner,
                
                # 信用信息
                "credit_limit": float(customer.credit_limit) if customer.credit_limit else None,
                "credit_granted_amount": float(customer.credit_granted_amount) if customer.credit_granted_amount else None,
                "credit_granted_start": customer.credit_granted_start.isoformat() if customer.credit_granted_start else None,
                "credit_granted_end": customer.credit_granted_end.isoformat() if customer.credit_granted_end else None,
                "account_status": customer.account_status,
                "credit_card_type": customer.credit_card_type,
                "credit_card_usage": float(customer.credit_card_usage) if customer.credit_card_usage else None,
                
                # 客户分类
                "customer_classification": customer.customer_classification,
                "business_type": customer.business_type,
                
                # 风险画像
                "risk_profile": {
                    "risk_level": customer_risk_profile.risk_level if customer_risk_profile else None,
                    "credit_score": float(customer_risk_profile.credit_score) if customer_risk_profile and customer_risk_profile.credit_score else None,
                    "credit_rating": customer_risk_profile.credit_rating if customer_risk_profile else None,
                    "credit_record": customer_risk_profile.credit_record if customer_risk_profile else None,
                    "default_history": customer_risk_profile.default_history if customer_risk_profile else None,
                    "debt_ratio": float(customer_risk_profile.debt_ratio) if customer_risk_profile and customer_risk_profile.debt_ratio else None,
                    "payment_capability": float(customer_risk_profile.payment_capability) if customer_risk_profile and customer_risk_profile.payment_capability else None,
                    "warning_level": customer_risk_profile.warning_level if customer_risk_profile else None,
                } if customer_risk_profile else None,
                
                # 客户偏好
                "preference": {
                    "preferred_term_months": customer_preferences.preferred_term_months if customer_preferences else None,
                    "preferred_amount": float(customer_preferences.preferred_amount) if customer_preferences and customer_preferences.preferred_amount else None,
                    "risk_tolerance": customer_preferences.risk_tolerance if customer_preferences else None,
                    "online_preference": customer_preferences.online_preference if customer_preferences else None,
                } if customer_preferences else None,
                
                # 贷款信息
                "loans": [
                    {
                        "loan_amount": float(loan.loan_amount) if loan.loan_amount else None,
                        "balance": float(loan.balance) if loan.balance else None,
                        "business_type": loan.business_type,
                        "loan_status": loan.loan_status,
                        "leading_rate": float(loan.leading_rate) if loan.leading_rate else None,
                        "loan_date": loan.loan_date.isoformat() if loan.loan_date else None,
                        "expir_date": loan.expir_date.isoformat() if loan.expir_date else None,
                        "product_name": loan.product_name,
                    }
                    for loan in customer_loans
                ],
                
                # 兼容旧版本字段
                "incomeLevel": customer.economic_stability or "中等收入",
                "assetLevel": customer.customer_classification or "普通客户", 
                "income": float(customer.annual_income)/12 if customer.annual_income else 0,
                "creditStatus": customer_risk_profile.credit_rating if customer_risk_profile else "未评估",
                "asset": float(customer.family_assets) if customer.family_assets else 0,
                "job": customer.occupation_type,
                "companyType": customer.employer_name,
                "riskLevel": customer_risk_profile.risk_level if customer_risk_profile else "medium",
                "creditScore": float(customer_risk_profile.credit_score) if customer_risk_profile and customer_risk_profile.credit_score else 0,
            }
                
            return user_info
            
        except Customer.DoesNotExist:
            logger.error(f"Customer not found with ID: {customer_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting customer info for {customer_id}: {str(e)}")
            return None 

    def _safe_float(self, value) -> Optional[float]:
        """
        安全地转换为float类型
        
        Args:
            value: 需要转换的值
            
        Returns:
            float值或None
        """
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None 