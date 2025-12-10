from typing import Dict, Any
import logging

from application.models.business import Customer
from .recommend import Recommend
from application.flow.step_node.recommend_node.i_recommend_node import IRecommendNode
from application.flow.i_step_node import NodeResult

logger = logging.getLogger('max_kb')

class BaseRecommendNode(IRecommendNode):
    """
    推荐节点
    """
    type = 'recommend-node'

    def valid_args(self, node_data: Dict[str, Any], workflow_params: Dict[str, Any]):
        """
        验证参数
        """
        logger.info(f"Validating args with node_data: {node_data}, workflow_params: {workflow_params}")
        super().valid_args(node_data, workflow_params)

    def save_context(self, details, workflow_manage):
        """
        保存上下文
        """
        logger.info(f"Saving context with details: {details}")
        self.context['user_info'] = details.get('user_info')
        self.context['recommend_list'] = details.get('recommend_list')
        self.context['run_time'] = details.get('run_time')

    def get_details(self, index: int, **kwargs):
        """
        获取详情
        """
        details = {
            'name': self.node.properties.get('stepName'),
            'index': index,
            'user_info': self.context.get('user_info'),
            'recommend_list': self.context.get('recommend_list'),
            'run_time': self.context.get('run_time'),
            'type': self.node.type,
            'status': self.status,
            'err_message': self.err_message
        }
        logger.info(f"Getting details: {details}")
        return details

    def execute(self, customer_id, **kwargs) -> NodeResult:
        """
        执行节点
        """
        logger.info(f"Executing recommend node with customer_id: {customer_id}, kwargs: {kwargs}")
        
        if not customer_id:
            logger.error("Customer ID is required but not provided")
            self.status = 400
            self.err_message = 'Customer ID is required'
            return NodeResult({}, {})

        try:
            # 获取推荐服务实例
            recommend_service = Recommend()
            
            # 使用优化方法同时获取客户信息和推荐列表，避免重复查询
            logger.info(f"Getting customer info and recommendations for ID: {customer_id}")
            result = recommend_service.get_customer_info_and_recommendations(customer_id)
            
            user_info = result.get("user_info")
            recommend_list = result.get("recommend_list", [])
            
            if not user_info:
                logger.error(f"Customer not found with ID: {customer_id}")
                self.status = 404
                self.err_message = 'Customer not found'
                return NodeResult({}, {})

            logger.info(f"Found customer: {user_info.get('name')}")
            logger.info(f"Got {len(recommend_list)} recommendations")

            # 返回结果
            node_variable = {
                'user_info': user_info,
                'recommend_list': recommend_list
            }
            
            logger.info(f"Returning node result with {len(recommend_list)} recommendations")
            return NodeResult(node_variable, {})
            
        except Exception as e:
            logger.error(f"Error in recommend node execution: {str(e)}", exc_info=True)
            self.status = 500
            self.err_message = str(e)
            return NodeResult({}, {}) 