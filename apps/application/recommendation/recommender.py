"""
金融产品推荐系统 - CustomerMarketing项目适配版
主要功能:
1. 特征处理: 处理客户和产品特征
2. 产品匹配: 基于规则的产品匹配
3. 高级推荐: 融合多种推荐策略(规则匹配、协同过滤、基于内容的推荐)
"""

import hashlib
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
import json
from scipy import stats
from .rules_engine import (
    ComplianceRulesEngine,
    RuleType,
    RuleSeverity
)
import logging
from typing import List, Dict, Any, Optional
from application.models.business import (
    Customer, Product, CustomerLoan, # CustomerPreference, 
    CustomerRiskProfile, # InteractionHistory
)

class RulesMatcher:
    """
    规则匹配类 - 适配CustMark项目模型
    主要功能:
    1. 基于规则的产品匹配
    2. 计算产品匹配分数
    3. 生成匹配理由
    """
    def __init__(self):
        pass
        
    def match_products(self, customer: Customer, customer_risk_profile: CustomerRiskProfile, products: List[Product]):
        """
        产品匹配主函数
        参数:
            customer: Customer对象
            customer_risk_profile: CustomerRiskProfile对象
            products: Product对象列表
        返回:
            matched_products: 匹配的产品列表，按匹配分数排序
        """
        matched_products = []
        
        for product in products:
            if self._basic_rules_match(customer, customer_risk_profile, product):
                match_score = self._calculate_match_score(customer, customer_risk_profile, product)
                matched_products.append({
                    'product': product,
                    'match_score': match_score
                })
        
        return sorted(matched_products, key=lambda x: x['match_score'], reverse=True)
        
    def _basic_rules_match(self, customer: Customer, risk_profile: CustomerRiskProfile, product: Product):
        """基础规则匹配"""
        # 1. 年龄检查
        if product.min_age and customer.age and customer.age < product.min_age:
            return False
        if product.max_age and customer.age and customer.age > product.max_age:
            return False
            
        # 2. 额度检查 - 使用yearly_income字段
        if product.min_amount and customer.annual_income:
            monthly_income = float(customer.annual_income) / 12
            if monthly_income < float(product.min_amount):
                return False
            
        # 3. 风险等级检查
        if risk_profile and risk_profile.risk_level == 'high' and product.product_type in ['定期存款', '保守型理财']:
            return True
            
        # 4. 区域限制检查
        if product.service_region and customer.household_address:
            if not any(region in customer.household_address for region in product.service_region.split(',')):
                return False
                
        return True
        
    def _calculate_match_score(self, customer: Customer, risk_profile: CustomerRiskProfile, product: Product):
        """计算匹配分数"""
        score = 0.0
        
        # 1. 收入匹配度 (30%)
        if customer.annual_income and product.max_amount:
            monthly_income = float(customer.annual_income) / 12
            income_score = min(monthly_income / float(product.max_amount), 1.0)
            score += 0.3 * income_score
            
        # 2. 风险匹配度 (30%)
        risk_score = self._calculate_risk_match(customer, risk_profile, product)
        score += 0.3 * risk_score
        
        # 3. 产品特征匹配度 (40%)
        feature_score = self._calculate_feature_match(customer, product)
        score += 0.4 * feature_score
        
        return score
        
    def _calculate_risk_match(self, customer: Customer, risk_profile: CustomerRiskProfile, product: Product):
        """计算风险匹配度"""
        if not risk_profile:
            return 0.5
            
        risk_level_map = {
            'low': 1,
            'medium': 2,
            'high': 3
        }
        
        product_risk = 1
        if product.product_description and '高风险' in product.product_description:
            product_risk = 3
        elif product.product_description and '中风险' in product.product_description:
            product_risk = 2
            
        customer_risk = risk_level_map.get(risk_profile.risk_level, 2)
        
        risk_diff = abs(customer_risk - product_risk)
        return 1.0 - (risk_diff / 2)
        
    def _calculate_feature_match(self, customer: Customer, product: Product):
        """计算产品特征匹配度"""
        score = 0.0
        
        # 1. 线上操作偏好匹配
        if all([product.online_application, product.online_approval,
               product.online_disbursement, product.online_repayment]):
            score += 0.25
            
        # 2. 职业匹配
        if product.target_customers and customer.occupation_type:
            if customer.occupation_type in product.target_customers:
                score += 0.25
                
        # 3. 期限匹配
        if customer.credit_granted_end and customer.credit_granted_start:
            preferred_term = (customer.credit_granted_end - customer.credit_granted_start).days / 30
            if product.min_term_months and product.max_term_months:
                if product.min_term_months <= preferred_term <= product.max_term_months:
                    score += 0.25
                
        # 4. 金额匹配
        if product.min_amount and customer.credit_granted_amount:
            if float(customer.credit_granted_amount) >= float(product.min_amount):
                score += 0.25
                
        return score

class CollaborativeFilteringRecommender:
    """协同过滤推荐器 - 适配CustMark项目模型"""
    
    def __init__(self):
        pass
        
    def recommend(self, customer: Customer, products: List[Product], interaction_history=None): # List[InteractionHistory]):
        """基于协同过滤的推荐"""
        if not interaction_history:
            return [0.5] * len(products)
            
        # 1. 构建用户-产品交互矩阵
        user_product_matrix = self._build_interaction_matrix(interaction_history)
        
        # 2. 计算用户相似度
        user_similarity = cosine_similarity(user_product_matrix)
        
        # 3. 为每个产品预测得分
        product_scores = []
        for product in products:
            # 获取相似用户对该产品的评分
            similar_users_scores = []
            for other_user_id, similarity in enumerate(user_similarity[customer.id]):
                if similarity > 0:
                    score = user_product_matrix[other_user_id][product.id]
                    if score > 0:
                        similar_users_scores.append(score * similarity)
                        
            # 计算加权平均分
            if similar_users_scores:
                product_scores.append(np.mean(similar_users_scores))
            else:
                product_scores.append(0.5)
                
        return product_scores
        
    def _build_interaction_matrix(self, interaction_history=None): # List[InteractionHistory]):
        """构建用户-产品交互矩阵"""
        # 获取所有唯一的用户ID和产品ID
        user_ids = sorted(set(ih.customer.id for ih in interaction_history if ih.customer))
        product_ids = sorted(set(ih.product_id for ih in interaction_history if ih.product_id))
        
        # 创建用户ID和产品ID的映射
        user_id_map = {uid: idx for idx, uid in enumerate(user_ids)}
        product_id_map = {pid: idx for idx, pid in enumerate(product_ids)}
        
        # 初始化矩阵
        matrix = np.zeros((len(user_ids), len(product_ids)))
                         
        for interaction in interaction_history:
            if interaction.customer and interaction.product_id:
                user_idx = user_id_map.get(interaction.customer.id)
                product_idx = product_id_map.get(interaction.product_id)
                
                if user_idx is not None and product_idx is not None:
                    score = 0.0
                    if interaction.interaction_type == 'view':
                        score = 0.2
                    elif interaction.interaction_type == 'click':
                        score = 0.4
                    elif interaction.interaction_type == 'apply':
                        score = 0.8
                    elif interaction.interaction_type == 'approve':
                        score = 1.0
                        
                    matrix[user_idx][product_idx] = score
            
        return matrix

class ContentBasedRecommender:
    """基于内容的推荐器 - 适配MaxKB项目模型"""
    
    def __init__(self):
        pass
        
    def recommend(self, customer: Customer, products: List[Product], customer_preferences=None): # CustomerPreference):
        """基于内容的推荐"""
        # 提取客户特征
        customer_features = self._extract_customer_features(customer, customer_preferences)
        
        scores = []
        for product in products:
            # 提取产品特征
            product_features = self._extract_product_features(product)
            
            # 计算相似度
            similarity = self._calculate_feature_similarity(customer_features, product_features)
            scores.append(similarity)
            
        return scores
        
    def _extract_customer_features(self, customer: Customer, preferences=None): # CustomerPreference):
        """提取客户特征向量"""
        features = {}
        
        # 基础特征
        features.update({
            'age': customer.age or 0,
            'income': float(customer.annual_income) if customer.annual_income else 0,
            # 'credit_limit': float(customer.credit_limit) if customer.credit_limit else 0,
        })
        
        # 偏好特征 - 暂时注释掉
        # if preferences:
        #     features.update({
        #         'preferred_term': preferences.preferred_term_months or 12,
        #         'preferred_amount': float(preferences.preferred_amount) if preferences.preferred_amount else 0,
        #         'risk_tolerance': preferences.risk_tolerance or 'medium',
        #         'online_preference': preferences.online_preference or False,
        #     })
        
        # 使用默认值代替偏好特征
        features.update({
            'preferred_term': 12,  # 默认12个月
            'preferred_amount': 0,  # 默认0
            'risk_tolerance': 'medium',  # 默认中等风险
            'online_preference': False,  # 默认不偏好线上
        })
            
        return features
        
    def _extract_product_features(self, product: Product):
        """提取产品特征向量"""
        features = {
            # 产品金额范围特征
            'min_amount': float(product.min_amount) if product.min_amount else 0,
            'max_amount': float(product.max_amount) if product.max_amount else 0,
            
            # 产品期限范围特征
            'min_term': product.min_term_months or 12,
            'max_term': product.max_term_months or 60,
            
            # 产品利率范围特征
            'min_interest_rate': float(product.min_interest_rate) if product.min_interest_rate else 0,
            'max_interest_rate': float(product.max_interest_rate) if product.max_interest_rate else 0,
            
            # 产品线上服务特征
            'is_online': all([
                product.online_application or False,
                product.online_approval or False,
                product.online_disbursement or False,
                product.online_repayment or False
            ]),
        }
        return features
        
    def _calculate_feature_similarity(self, customer_features: Dict, product_features: Dict):
        """计算特征相似度"""
        score = 0.0
        
        # 1. 金额匹配度
        if 'preferred_amount' in customer_features:
            preferred_amount = customer_features['preferred_amount']
            if product_features['min_amount'] <= preferred_amount <= product_features['max_amount']:
                score += 0.3
                
        # 2. 期限匹配度
        if 'preferred_term' in customer_features:
            preferred_term = customer_features['preferred_term']
            if product_features['min_term'] <= preferred_term <= product_features['max_term']:
                score += 0.3
                
        # 3. 线上操作偏好匹配度
        if 'online_preference' in customer_features:
            if customer_features['online_preference'] == product_features['is_online']:
                score += 0.2
                
        # 4. 收入与额度匹配度
        income = customer_features['income']
        if income >= product_features['min_amount'] * 12:
            score += 0.2
            
        return score

class ImprovedCollaborativeFilteringRecommender:
    """改进的协同过滤推荐器"""
    
    def __init__(self):
        self.user_factors = None
        self.item_factors = None
        self.n_factors = 10  # 潜在因子数量
        
    def recommend(self, customer, products, interaction_history):
        """基于协同过滤的推荐"""
        if not interaction_history:
            return [0.5] * len(products)
            
        # 1. 构建用户-产品交互矩阵
        user_product_matrix = self._build_interaction_matrix(interaction_history)
        
        # 2. 使用矩阵分解进行协同过滤
        self._matrix_factorization(user_product_matrix)
        
        # 3. 为每个产品预测得分
        product_scores = []
        for product in products:
            try:
                # 确保customer_id和product_id在矩阵范围内
                if (hasattr(customer, 'customer_id') and customer.customer_id < self.user_factors.shape[0] and
                    hasattr(product, 'product_id') and product.product_id < self.item_factors.shape[0]):
                    # 使用潜在因子进行评分预测
                    user_vector = self.user_factors[customer.customer_id]
                    product_vector = self.item_factors[product.product_id]
                    score = np.dot(user_vector, product_vector)
                    # 将分数归一化到0-1范围
                    score = max(0, min(1, score))
                else:
                    score = 0.5  # 对于没有历史数据的产品或用户，使用默认值
            except (AttributeError, IndexError):
                score = 0.5  # 如果出现任何错误，使用默认值
                
            product_scores.append(score)
                
        return product_scores
    
    def _build_interaction_matrix(self, interaction_history):
        """构建用户-产品交互矩阵，加入时间衰减因子"""
        if not interaction_history:
            return np.zeros((1, 1))  # 返回1x1的零矩阵作为默认值
            
        try:
            max_user_id = max(ih.customer.id for ih in interaction_history if hasattr(ih, 'customer_id')) + 1
            max_product_id = max(ih.product_id for ih in interaction_history if hasattr(ih, 'product_id')) + 1
        except ValueError:  # 如果没有有效的customer_id或product_id
            return np.zeros((1, 1))
            
        matrix = np.zeros((max_user_id, max_product_id))
        
        # 获取当前时间
        current_time = datetime.now()
        
        for interaction in interaction_history:
            try:
                # 基础分数设置
                base_score = 0.0
                if interaction.interaction_type == 'view':
                    base_score = 0.2
                elif interaction.interaction_type == 'click':
                    base_score = 0.4
                elif interaction.interaction_type == 'apply':
                    base_score = 0.8
                elif interaction.interaction_type == 'approve':
                    base_score = 1.0
                
                # 计算时间衰减因子 (半衰期为30天)
                days_passed = (current_time - interaction.interaction_time).days
                time_decay = np.exp(-0.023 * days_passed)  # 约30天衰减到一半
                
                # 最终分数 = 基础分数 * 时间衰减因子
                final_score = base_score * time_decay
                
                # 确保索引有效
                if hasattr(interaction, 'customer_id') and hasattr(interaction, 'product_id'):
                    if 0 <= interaction.customer_id < max_user_id and 0 <= interaction.product_id < max_product_id:
                        # 如果存在多次交互，保留最高分
                        current_score = matrix[interaction.customer_id][interaction.product_id]
                        matrix[interaction.customer_id][interaction.product_id] = max(current_score, final_score)
            except (AttributeError, IndexError):
                continue  # 跳过无效的交互记录
        
        return matrix
    
    def _matrix_factorization(self, R, steps=100, alpha=0.01, beta=0.01):
        """
        矩阵分解算法 - 使用随机梯度下降优化
        R: 用户-产品交互矩阵
        """
        # 获取矩阵维度
        n_users, n_items = R.shape
        
        # 如果已经有因子矩阵且维度匹配，则重用
        if self.user_factors is not None and self.user_factors.shape == (n_users, self.n_factors):
            pass
        else:
            # 初始化潜在因子矩阵
            self.user_factors = np.random.rand(n_users, self.n_factors) * 0.1
            self.item_factors = np.random.rand(n_items, self.n_factors) * 0.1
        
        # 训练模型
        for step in range(steps):
            for u in range(n_users):
                for i in range(n_items):
                    if R[u, i] > 0:  # 只对有交互的评分进行学习
                        # 计算预测误差
                        prediction = np.dot(self.user_factors[u], self.item_factors[i])
                        error = R[u, i] - prediction
                        
                        # 更新潜在因子
                        for k in range(self.n_factors):
                            self.user_factors[u, k] += alpha * (2 * error * self.item_factors[i, k] - beta * self.user_factors[u, k])
                            self.item_factors[i, k] += alpha * (2 * error * self.user_factors[u, k] - beta * self.item_factors[i, k])
        
        # 为了稳定性，限制值范围
        self.user_factors = np.clip(self.user_factors, -1, 1)
        self.item_factors = np.clip(self.item_factors, -1, 1)


class LoanHistoryRecommender:
    """
    基于贷款历史的推荐器 - 适配MaxKB项目模型
    利用客户的历史贷款数据进行产品推荐
    """
    def __init__(self):
        pass
        
    def recommend(self, customer: Customer, products: List[Product], customer_loans: List[CustomerLoan]):
        """
        基于历史贷款数据的推荐
        Args:
            customer: Customer对象
            products: 待推荐产品列表
            customer_loans: 客户历史贷款数据列表
        """
        if not customer_loans:
            return [0.5] * len(products)
            
        # 1. 构建用户-产品矩阵
        user_product_matrix = self._build_loan_matrix(customer_loans)
        
        # 检查矩阵是否为空或无效
        if user_product_matrix.shape[0] == 0 or user_product_matrix.shape[1] == 0:
            return [0.5] * len(products)
        
        # 2. 计算用户相似度
        try:
            user_similarity = cosine_similarity(user_product_matrix)
        except ValueError:
            # 如果矩阵太小或有问题，返回默认分数
            return [0.5] * len(products)
        
        # 3. 为每个产品预测得分
        product_scores = []
        for product in products:
            # 获取相似用户对该产品的评分
            similar_users_scores = []
            
            # 使用客户的身份证号来查找在矩阵中的位置
            customer_cert_id = customer.cert_id
            if not customer_cert_id:
                # 如果没有身份证号，使用默认分数
                product_scores.append(0.5)
                continue
            
            # 找到客户在矩阵中的索引
            cert_ids = sorted(set(loan.cert_id for loan in customer_loans if loan.cert_id))
            if customer_cert_id not in cert_ids:
                # 如果客户不在矩阵中，使用默认分数
                product_scores.append(0.5)
                continue
                
            customer_idx = cert_ids.index(customer_cert_id)
            
            # 检查索引是否在范围内
            if customer_idx >= user_similarity.shape[0]:
                product_scores.append(0.5)
                continue
                
            for other_cert_idx, similarity in enumerate(user_similarity[customer_idx]):
                if similarity > 0:
                    other_cert_id = cert_ids[other_cert_idx] if other_cert_idx < len(cert_ids) else None
                    if other_cert_id:
                        score = self._calculate_product_score(
                            customer_loans, 
                            other_cert_id, 
                            product.product_name
                        )
                        if score > 0:
                            similar_users_scores.append(score * similarity)
                        
            # 计算加权平均分
            if similar_users_scores:
                product_scores.append(np.mean(similar_users_scores))
            else:
                product_scores.append(0.5)
                
        return product_scores
        
    def _build_loan_matrix(self, customer_loans: List[CustomerLoan]):
        """
        构建用户-产品矩阵(基于历史贷款数据)
        矩阵中的值基于以下因素加权计算:
        1. 贷款金额 - 金额越大，权重越高 (0.3)
        2. 贷款时间 - 最近的贷款权重更高 (0.2)
        3. 还款情况 - 正常还款的权重更高 (0.2)
        4. 贷款利率 - 利率越低，权重越高 (0.3)
        """
        # 过滤掉没有产品名称的贷款记录
        valid_loans = [loan for loan in customer_loans if loan.cert_id and loan.product_name]
        
        if not valid_loans:
            # 如果没有有效的贷款记录，返回默认矩阵
            return np.zeros((1, 1))
        
        # 获取所有唯一的身份证号和产品名称
        cert_ids = sorted(set(loan.cert_id for loan in valid_loans))
        product_names = sorted(set(loan.product_name for loan in valid_loans))
        
        # 创建身份证号和产品名称的映射
        cert_id_map = {cert_id: idx for idx, cert_id in enumerate(cert_ids)}
        product_name_map = {name: idx for idx, name in enumerate(product_names)}
        
        # 初始化矩阵
        matrix = np.zeros((len(cert_ids), len(product_names)))
        
        # 当前日期(用于计算时间权重)
        current_date = datetime.now()
        
        # 计算产品平均利率，用于比较
        product_avg_rates = {}
        for product_name in product_names:
            relevant_loans = [loan for loan in valid_loans if loan.product_name == product_name]
            if relevant_loans:
                rates = [float(loan.leading_rate) for loan in relevant_loans if loan.leading_rate]
                if rates:
                    product_avg_rates[product_name] = sum(rates) / len(rates)
                else:
                    product_avg_rates[product_name] = 0
            else:
                product_avg_rates[product_name] = 0
                
        # 市场平均利率(可以替换为实际的市场平均利率)
        market_avg_rate = sum(product_avg_rates.values()) / len(product_avg_rates) if product_avg_rates else 0
        
        for loan in valid_loans:
            cert_idx = cert_id_map.get(loan.cert_id)
            product_idx = product_name_map.get(loan.product_name)
            
            if cert_idx is not None and product_idx is not None:
                # 1. 计算金额权重 (0.3)
                amount_weight = min(float(loan.loan_amount or 0) / 1000000, 1.0) * 0.3
                
                # 2. 计算时间权重 (0.2)
                if loan.loan_date:
                    days_diff = (current_date - loan.loan_date).days
                    time_weight = max(1 - (days_diff / 365), 0) * 0.2
                else:
                    time_weight = 0.1
                
                # 3. 计算还款情况权重 (0.2)
                if loan.balance and loan.balance > 0:
                    repayment_weight = 0.2  # 正在还款中
                else:
                    repayment_weight = 0.1  # 已结清
                    
                # 4. 计算利率权重 (0.3)
                if loan.leading_rate:
                    interest_rate = float(loan.leading_rate)
                    # 使用产品平均利率或市场平均利率进行比较
                    avg_rate = product_avg_rates.get(loan.product_name, market_avg_rate)
                    if avg_rate > 0:
                        # 利率低于平均值时给予更高权重
                        rate_ratio = avg_rate / interest_rate
                        rate_weight = min(rate_ratio, 1.5) * 0.3
                    else:
                        rate_weight = 0.15  # 默认中等权重
                else:
                    rate_weight = 0.15  # 默认中等权重
                    
                # 合并所有权重
                total_weight = amount_weight + time_weight + repayment_weight + rate_weight
                matrix[cert_idx][product_idx] = total_weight
        
        return matrix
        
    def _calculate_product_score(self, customer_loans: List[CustomerLoan], cert_id: str, product_name: str):
        """
        计算特定用户对特定产品的得分
        """
        relevant_loans = [
            loan for loan in customer_loans 
            if loan.cert_id == cert_id and loan.product_name == product_name
        ]
        
        if not relevant_loans:
            return 0
            
        # 使用最近的一笔贷款的评分
        latest_loan = max(relevant_loans, key=lambda x: x.loan_date or datetime.min)
        
        # 基础分数 0.5
        score = 0.5
        
        # 根据贷款金额调整分数 (最多+0.15)
        if latest_loan.loan_amount:
            amount_score = min(float(latest_loan.loan_amount) / 1000000, 0.15)
            score += amount_score
        
        # 根据还款情况调整分数 (最多+0.15)
        if latest_loan.balance:
            if float(latest_loan.balance) == 0:  # 已结清
                score += 0.15
            elif float(latest_loan.balance) < float(latest_loan.loan_amount or 0):  # 正常还款中
                score += 0.1
                
        # 根据利率调整分数 (最多+0.2)
        if latest_loan.leading_rate:
            interest_rate = float(latest_loan.leading_rate)
            # 利率越低，分数越高
            if interest_rate > 0:
                # 假设市场平均利率为5%，可以根据实际情况调整
                market_avg_rate = 5.0
                rate_score = min(market_avg_rate / interest_rate * 0.1, 0.2)
                score += rate_score
            
        return score

class AdvancedRecommender:
    """
    高级推荐类 - 适配MaxKB项目模型
    主要功能:
    1. 融合多种推荐策略
    2. 协同过滤推荐
    3. 基于内容的推荐
    4. 生成推荐理由
    """
    def __init__(self):
        self.product_matcher = RulesMatcher()
        self.content_recommender = ContentBasedRecommender()
        self.loan_history_recommender = LoanHistoryRecommender()
        
    def recommend(self, customer: Customer, customer_risk_profile: CustomerRiskProfile, products: List[Product], 
                 customer_preferences=None, interaction_history=None, # CustomerPreference = None, 
                 customer_loans: List[CustomerLoan] = None, top_n: int = 5):
        """多策略融合推荐主函数"""
        
        # 1. 规则匹配得分
        rule_based_scores = []
        for product in products:
            score = self.product_matcher._calculate_match_score(
                customer, customer_risk_profile, product
            )
            rule_based_scores.append(score)
            
        # 2. 协同过滤得分(基于交互历史) - 暂时注释
        cf_scores = [0.5] * len(products)  # 使用默认值代替
        
        # 3. 基于内容的推荐得分
        content_scores = self.content_recommender.recommend(
            customer, products, customer_preferences  # 传入None或默认值
        )
        
        # 4. 基于贷款历史的推荐得分
        loan_history_scores = self.loan_history_recommender.recommend(
            customer, products, customer_loans or []
        )
        
        # 5. 融合所有得分
        final_scores = []
        for i, product in enumerate(products):
            final_score = (
                0.4 * rule_based_scores[i] +     # 规则匹配权重
                0.2 * content_scores[i] +        # 基于内容权重
                0.4 * loan_history_scores[i]     # 贷款历史权重
            )
            final_scores.append({
                'product': product,
                'score': final_score,
                'rule_score': rule_based_scores[i],
                'content_score': content_scores[i],
                'loan_history_score': loan_history_scores[i]
            })
            
        # 6. 排序并选择top_n个推荐
        final_scores.sort(key=lambda x: x['score'], reverse=True)
        recommendations = []
        
        for item in final_scores[:top_n]:
            reason = self._generate_recommendation_reason(
                customer,
                item['product'],
                item['rule_score'],
                item['content_score'],
                item['loan_history_score']
            )
            
            # 将Product对象转换为可序列化的字典
            product = item['product']
            product_dict = {
                'product_id': product.id,
                'product_name': product.product_name,
                'product_type': product.product_type,
                'product_description': product.product_description,
                'min_amount': float(product.min_amount) if product.min_amount else None,
                'max_amount': float(product.max_amount) if product.max_amount else None,
                'min_term_months': product.min_term_months,
                'max_term_months': product.max_term_months,
                'min_interest_rate': float(product.min_interest_rate) if product.min_interest_rate else None,
                'max_interest_rate': float(product.max_interest_rate) if product.max_interest_rate else None,
                'risk_level': product.risk_level,
                'online_application': product.online_application,
                'online_approval': product.online_approval,
                'online_disbursement': product.online_disbursement,
                'online_repayment': product.online_repayment
            }
            
            recommendations.append({
                'product': product_dict,
                'score': round(item['score'], 4),  # 保留4位小数
                'reason': reason
            })
            
        return recommendations
        
    def _generate_recommendation_reason(self, customer: Customer, product: Product, rule_score: float, 
                                      content_score: float, loan_history_score: float):
        """生成推荐理由"""
        reasons = []
        
        # 1. 基于规则匹配
        if rule_score > 0.8:
            reasons.append("该产品与您的基本条件非常匹配")
        elif rule_score > 0.6:
            reasons.append("该产品基本符合您的申请条件")
            
        # 2. 基于产品特征
        if product.online_application and product.online_approval:
            reasons.append("支持全线上办理，快速便捷")
            
        if product.min_interest_rate and float(product.min_interest_rate) < 0.1:
            reasons.append(f"最低年化利率{float(product.min_interest_rate)*100:.1f}%，利率优惠")
            
        # 3. 基于客户特征
        if customer.annual_income and product.min_amount:
            monthly_income = float(customer.annual_income) / 12
            if monthly_income > float(product.min_amount):
                reasons.append("您的收入条件完全满足要求")
            
        # 4. 基于贷款历史
        if loan_history_score > 0.8:
            reasons.append("根据您的历史贷款记录，该产品非常适合您")
        elif loan_history_score > 0.6:
            reasons.append("该产品与您过往选择的贷款产品类似")
            
        return "；".join(reasons)

class ImprovedAdvancedRecommender:
    """
    改进的高级推荐类 - 适配MaxKB项目模型
    主要功能:
    1. 融合多种推荐策略，动态调整权重
    2. 改进的协同过滤推荐
    3. 基于内容的推荐
    4. 基于贷款历史的推荐
    5. 合规性验证
    6. 生成全面的推荐理由
    """
    def __init__(self):
        self.product_matcher = RulesMatcher()
        self.cf_recommender = CollaborativeFilteringRecommender()
        self.content_recommender = ContentBasedRecommender()
        self.loan_history_recommender = LoanHistoryRecommender()
        self.compliance_engine = ComplianceRulesEngine()
        self.logger = logging.getLogger(__name__)
        
    def recommend(self, customer: Customer, customer_risk_profile: CustomerRiskProfile, products: List[Product], 
                 customer_preferences=None, interaction_history=None, # CustomerPreference = None, 
                 customer_loans: List[CustomerLoan] = None, top_n: int = 5):
        """动态权重融合推荐主函数"""
        try:
            # 1. 客户资质合规验证
            qualification_results = self.compliance_engine.validate(
                context={
                    "customer": self._customer_to_dict(customer),
                    "risk_profile": self._risk_profile_to_dict(customer_risk_profile) if customer_risk_profile else None,
                    # "preferences": self._preferences_to_dict(customer_preferences) if customer_preferences else None  # 注释掉偏好相关
                },
                rule_types=[RuleType.CUSTOMER_QUALIFICATION]
            )
            
            if not self._all_rules_passed(qualification_results):
                return {
                    "status": "failed",
                    "reason": "customer_qualification_check_failed",
                    "details": qualification_results
                }

            # 2. 收集各推荐器的得分
            rule_based_scores = []
            for product in products:
                score = self.product_matcher._calculate_match_score(
                    customer, customer_risk_profile, product
                )
                rule_based_scores.append(score)
                
            cf_scores = self.cf_recommender.recommend(
                customer, products, interaction_history or []
            )
            
            content_scores = self.content_recommender.recommend(
                customer, products, customer_preferences
            )
            
            loan_history_scores = self.loan_history_recommender.recommend(
                customer, products, customer_loans or []
            )
            
            # 3. 动态计算权重
            weights = self._calculate_dynamic_weights(
                customer, 
                interaction_history, 
                customer_loans
            )
            
            # 4. 对每个产品进行合规检查和评分融合
            final_scores = []
            for i, product in enumerate(products):
                # 产品合规性检查
                if self._validate_product_compliance(customer, customer_risk_profile, product):
                    final_score = (
                        weights['rule'] * rule_based_scores[i] +
                        weights['cf'] * cf_scores[i] +
                        weights['content'] * content_scores[i] +
                        weights['loan_history'] * loan_history_scores[i]
                    )
                    final_scores.append({
                        'product': product,
                        'score': final_score,
                        'rule_score': rule_based_scores[i],
                        'cf_score': cf_scores[i],
                        'content_score': content_scores[i],
                        'loan_history_score': loan_history_scores[i]
                    })
            
            # 5. 如果没有合规的产品，返回空列表
            if not final_scores:
                return {
                    "status": "success",
                    "recommendations": [],
                    "message": "未找到符合条件的产品"
                }
            
            # 6. 排序并选择top_n个推荐
            final_scores.sort(key=lambda x: x['score'], reverse=True)
            recommendations = self._format_recommendations(customer, final_scores[:top_n])
            
            return {
                "status": "success",
                "recommendations": recommendations,
                "compliance_status": "passed"
            }

        except Exception as e:
            self.logger.error(f"Product recommendation failed: {str(e)}")
            return {
                "status": "error",
                "reason": str(e)
            }

    def _validate_product_compliance(self, customer: Customer, customer_risk_profile: CustomerRiskProfile, product: Product) -> bool:
        """
        验证产品是否符合合规要求
        """
        try:
            # 1. 产品准入规则验证
            eligibility_results = self.compliance_engine.validate(
                context={
                    "customer": self._customer_to_dict(customer),
                    "risk_profile": self._risk_profile_to_dict(customer_risk_profile) if customer_risk_profile else None,
                    "product": self._product_to_dict(product)
                },
                rule_types=[RuleType.PRODUCT_ELIGIBILITY]
            )
            if not self._all_rules_passed(eligibility_results):
                return False

            # 2. 风险控制规则验证
            risk_results = self.compliance_engine.validate(
                context={
                    "customer": self._customer_to_dict(customer),
                    "risk_profile": self._risk_profile_to_dict(customer_risk_profile) if customer_risk_profile else None,
                    "product": self._product_to_dict(product)
                },
                rule_types=[RuleType.RISK_CONTROL]
            )
            if not self._all_rules_passed(risk_results):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Product compliance validation failed: {str(e)}")
            return False

    def _format_recommendations(self, customer: Customer, scored_products: List[Dict]):
        """格式化推荐结果"""
        recommendations = []
        
        for item in scored_products:
            # 生成推荐理由
            reason = self._generate_comprehensive_reason(
                customer,
                item['product'],
                item['rule_score'],
                item['cf_score'],
                item['content_score'],
                item['loan_history_score']
            )
            
            # 将Product对象转换为可序列化的字典
            product_dict = self._product_to_dict(item['product'])
            
            recommendations.append({
                'product': product_dict,
                'score': round(item['score'], 4),
                'reason': reason
            })
            
        return recommendations

    def _customer_to_dict(self, customer: Customer) -> Dict[str, Any]:
        """将Customer对象转换为字典"""
        try:
            return {
                'id': customer.id,
                'name': customer.name,
                'age': customer.age,
                'income': float(customer.annual_income) if customer.annual_income else 0.0,
                'monthly_income': float(customer.annual_income) / 12 if customer.annual_income else None,
                'credit_score': getattr(customer, 'credit_score', None),
                'occupation': customer.occupation_type,
                'company_type': customer.employer_name,
                'work_start_date': customer.work_start_date,
                'address': customer.household_address,
                # 'region': customer.region,
                # 'industry_type': customer.industry_type,
                # 'credit_limit': float(customer.credit_limit) if customer.credit_limit else 0,
                # 'position': customer.position,
                # 'family_yearly_income': float(customer.family_yearly_income) if customer.family_yearly_income else None,
                # 'credit_granted_amount': float(customer.credit_granted_amount) if customer.credit_granted_amount else None,
                # 'credit_granted_start': customer.credit_granted_start,
                # 'credit_granted_end': customer.credit_granted_end
            }
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error converting customer data: {str(e)}")
            return {
                'id': customer.id,
                'name': customer.name,
                'age': customer.age,
                'income': 0.0,
                'monthly_income': 0.0
            }

    def _risk_profile_to_dict(self, risk_profile: CustomerRiskProfile) -> Dict[str, Any]:
        """将CustomerRiskProfile对象转换为字典"""
        if not risk_profile:
            return {}
        
        try:
            return {
                'credit_score': float(risk_profile.credit_score) if risk_profile.credit_score else None,
                'risk_level': risk_profile.risk_level,
                'default_history': risk_profile.default_history,
                'debt_ratio': float(risk_profile.debt_ratio) if risk_profile.debt_ratio else None,
                'payment_capability': float(risk_profile.payment_capability) if risk_profile.payment_capability else None,
                'credit_rating': risk_profile.credit_rating,
                'credit_record': risk_profile.credit_record,
                'personal_credit_record': risk_profile.personal_credit_record,
                'default_times': risk_profile.default_times,
                'has_loan_history': risk_profile.has_loan_history,
                'risk_preference': risk_profile.risk_preference,
                'warning_level': risk_profile.warning_level,
                'external_guarantee_amount': float(risk_profile.external_guarantee_amount) if risk_profile.external_guarantee_amount else None,
                'bank_relationship': risk_profile.bank_relationship
            }
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error converting risk profile data: {str(e)}")
            return {}

    # def _preferences_to_dict(self, preferences: CustomerPreference) -> Dict[str, Any]:
    #     """将CustomerPreference对象转换为字典"""
    #     if not preferences:
    #         return {}
    #     
    #     try:
    #         return {
    #             'preferred_term_months': preferences.preferred_term_months,
    #             'preferred_amount': float(preferences.preferred_amount) if preferences.preferred_amount else None,
    #             'risk_tolerance': preferences.risk_tolerance,
    #             'online_preference': preferences.online_preference
    #         }
    #     except (ValueError, TypeError) as e:
    #         self.logger.error(f"Error converting preferences data: {str(e)}")
    #         return {}

    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """将Product对象转换为字典"""
        return {
            'id': product.id,
            'product_name': product.product_name,
            'product_type': product.product_type,
            'product_description': product.product_description,
            'min_amount': float(product.min_amount) if product.min_amount else None,
            'max_amount': float(product.max_amount) if product.max_amount else None,
            'min_term_months': product.min_term_months,
            'max_term_months': product.max_term_months,
            'min_interest_rate': float(product.min_interest_rate) if product.min_interest_rate else None,
            'max_interest_rate': float(product.max_interest_rate) if product.max_interest_rate else None,
            'min_age': product.min_age,
            'max_age': product.max_age,
            'risk_level': product.risk_level,
            'target_customers': product.target_customers,
            'service_region': product.service_region,
            'online_application': product.online_application,
            'online_approval': product.online_approval,
            'online_disbursement': product.online_disbursement,
            'online_repayment': product.online_repayment
        }

    def _all_rules_passed(self, results: List[Dict[str, Any]]) -> bool:
        """检查是否所有规则都通过"""
        return all(result.get("is_valid", False) for result in results)

    def _calculate_dynamic_weights(self, customer: Customer, interaction_history=None, customer_loans=None): # List[InteractionHistory], List[CustomerLoan]):
        """
        动态计算各推荐器的权重
        根据用户的历史数据可用性和质量调整权重
        """
        # 默认权重
        weights = {
            'rule': 0.35,
            'cf': 0.20,
            'content': 0.20,
            'loan_history': 0.25
        }
        
        # 1. 如果没有交互历史，降低CF权重
        if not interaction_history:
            weights['cf'] = 0.05
            # 重新分配权重
            weights['rule'] += 0.05
            weights['content'] += 0.05
            weights['loan_history'] += 0.05
        
        # 2. 如果有丰富的贷款历史，提高贷款历史推荐器权重
        if customer_loans and len(customer_loans) > 3:
            weights['loan_history'] = 0.35
            # 重新分配权重
            weights['rule'] -= 0.05
            weights['cf'] -= 0.05
        
        # 3. 根据客户年龄调整内容推荐权重
        if customer.age and customer.age < 30:  # 年轻用户更看重产品特性
            weights['content'] += 0.05
            weights['rule'] -= 0.05
        
        # 确保权重总和为1
        total = sum(weights.values())
        for key in weights:
            weights[key] /= total
            
        return weights

    def _generate_comprehensive_reason(self, customer: Customer, product: Product, rule_score: float, 
                                     cf_score: float, content_score: float, loan_history_score: float):
        """生成更全面的推荐理由"""
        reasons = []
        
        # 1. 基于规则匹配
        if rule_score > 0.8:
            reasons.append("该产品与您的基本条件非常匹配")
        elif rule_score > 0.6:
            reasons.append("该产品基本符合您的申请条件")
            
        # 2. 基于协同过滤
        if cf_score > 0.8:
            reasons.append("很多与您相似的客户都选择了该产品")
        elif cf_score > 0.6:
            reasons.append("该产品受到相似客户的欢迎")
            
        # 3. 基于产品特征
        if content_score > 0.8:
            reasons.append("该产品特性与您的偏好高度匹配")
        elif content_score > 0.6:
            reasons.append("该产品特性基本符合您的偏好")
            
        # 4. 基于贷款历史
        if loan_history_score > 0.8:
            reasons.append("根据您的历史贷款记录，该产品非常适合您")
        elif loan_history_score > 0.6:
            reasons.append("该产品与您过往选择的贷款产品类似")
        
        # 5. 产品亮点说明
        self._add_product_highlights(product, reasons)
        
        # 6. 个性化触发因素
        self._add_personalized_triggers(customer, product, reasons)
            
        return "；".join(reasons)
    
    def _add_product_highlights(self, product: Product, reasons: List[str]):
        """添加产品亮点说明"""
        if product.online_application and product.online_approval:
            reasons.append("支持全线上办理，快速便捷")
            
        if product.min_interest_rate and float(product.min_interest_rate) < 0.1:
            reasons.append(f"最低年化利率{float(product.min_interest_rate)*100:.1f}%，利率优惠")
            
        if product.min_term_months and product.min_term_months < 6:
            reasons.append("支持短期借款，灵活性高")
    
    def _add_personalized_triggers(self, customer: Customer, product: Product, reasons: List[str]):
        """添加个性化触发因素"""
        if customer.annual_income and product.min_amount:
            monthly_income = float(customer.annual_income) / 12
            if monthly_income > float(product.min_amount) * 2:
                reasons.append("您的收入条件优越，贷款审批率较高")
            
        if customer.age and customer.age < 35 and product.product_description and "年轻客户专享" in product.product_description:
            reasons.append("年轻客户专享优惠")

class ProductRecommender:
    """
    产品推荐器主类 - 适配MaxKB项目模型
    提供统一的推荐接口，整合所有推荐策略
    """
    def __init__(self):
        self.advanced_recommender = ImprovedAdvancedRecommender()
        self.logger = logging.getLogger(__name__)
        
    def recommend_products(self, customer: Customer, products: List[Product], 
                          customer_risk_profile: CustomerRiskProfile = None,
                          customer_preferences=None,  # CustomerPreference = None,
                          interaction_history=None,
                          customer_loans: List[CustomerLoan] = None,
                          top_n: int = 5):
        """
        产品推荐主接口
        Args:
            customer: Customer对象
            products: 待推荐产品列表
            customer_risk_profile: 客户风险画像
            customer_preferences: 客户偏好 (暂时不使用)
            interaction_history: 交互历史
            customer_loans: 贷款历史
            top_n: 推荐数量
        Returns:
            推荐结果字典
        """
        try:
            # 1. 参数验证
            if not customer or not products:
                return {
                    "status": "error",
                    "reason": "客户信息或产品列表不能为空"
                }
                
            # 2. 调用高级推荐器
            result = self.advanced_recommender.recommend(
                customer=customer,
                customer_risk_profile=customer_risk_profile,
                products=products,
                customer_preferences=customer_preferences,
                interaction_history=interaction_history,
                customer_loans=customer_loans,
                top_n=top_n
            )
            
            # 3. 添加推荐统计信息
            if result["status"] == "success":
                result["statistics"] = self._generate_recommendation_statistics(
                    customer, result["recommendations"]
                )
                
            return result
            
        except Exception as e:
            self.logger.error(f"Product recommendation failed: {str(e)}")
            return {
                "status": "error",
                "reason": f"推荐系统异常: {str(e)}"
            }
            
    def _generate_recommendation_statistics(self, customer: Customer, recommendations: List[Dict]):
        """生成推荐统计信息"""
        if not recommendations:
            return {}
            
        # 计算推荐产品的统计信息
        total_products = len(recommendations)
        avg_score = sum(rec["score"] for rec in recommendations) / total_products
        max_score = max(rec["score"] for rec in recommendations)
        min_score = min(rec["score"] for rec in recommendations)
        
        # 产品类型分布
        product_types = {}
        for rec in recommendations:
            product_type = rec["product"]["product_type"]
            product_types[product_type] = product_types.get(product_type, 0) + 1
            
        # 线上服务统计
        online_products = sum(
            1 for rec in recommendations 
            if rec["product"]["online_application"] and rec["product"]["online_approval"]
        )
        
        return {
            "total_recommendations": total_products,
            "average_score": round(avg_score, 4),
            "max_score": round(max_score, 4),
            "min_score": round(min_score, 4),
            "product_type_distribution": product_types,
            "online_service_ratio": round(online_products / total_products, 2) if total_products > 0 else 0
        }

 