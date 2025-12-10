# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： third_party_customer.py
    @date：2024/12/19 16:00
    @desc: 第三方客户信息获取服务
"""

import requests
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse
from application.models.business import Customer, CustomerLoan
from application.models.config import get_config

logger = logging.getLogger(__name__)


def log_api_call(func: Callable) -> Callable:
    """装饰器: 记录API调用的日志"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"开始调用: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"调用完成: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"调用异常: {func.__name__} - {str(e)}", exc_info=True)
            raise
    return wrapper


class ThirdPartyCustomerClient:
    """第三方客户信息客户端"""
    
    # 默认配置常量
    DEFAULT_HEADERS = {'Content-Type': 'application/json'}
    DEFAULT_REQUEST_TIMEOUT = 60  # 增加超时时间到60秒
    
    # 默认接口URL配置
    DEFAULT_API_URLS = {
        'get_custom_loan': '/restcloud/aiapiapplicatio/getCustomLoan',
        'get_customer_info': '/restcloud/aiapiapplicatio/getCustomInfo',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
    
    @property
    def api_base_url(self) -> Optional[str]:
        """从数据库获取API基础URL，并进行规范化处理"""
        url = get_config('third_party_api_base_url')
        if url is None:
            logger.warning("数据库中没有配置 third_party_api_base_url，请先配置该参数")
            return None
        # 规范化URL：去除末尾的点、空格等
        url = url.rstrip('. \t\n\r')
        # 确保URL末尾没有斜杠（除非是根路径）
        if url.endswith('/') and url != 'http://' and url != 'https://':
            url = url.rstrip('/')
        return url
    
    @property
    def request_timeout(self) -> int:
        """从数据库获取请求超时时间"""
        return get_config('third_party_request_timeout', self.DEFAULT_REQUEST_TIMEOUT)
    
    @property
    def headers(self) -> Dict[str, str]:
        """从数据库获取请求头"""
        headers = get_config('third_party_headers', self.DEFAULT_HEADERS)
        if isinstance(headers, dict):
            return headers
        return self.DEFAULT_HEADERS
    
    def get_api_url(self, api_name: str) -> str:
        """
        获取指定接口的完整URL
        :param api_name: 接口名称
        :return: 完整的API URL
        """
        # 优先从数据库获取接口URL
        config_key = f'third_party_api_url_{api_name}'
        api_path = get_config(config_key, self.DEFAULT_API_URLS.get(api_name, ''))
        
        # 规范化api_path
        api_path = api_path.strip()
        
        if api_path.startswith('http'):
            # 如果配置的是完整URL，直接返回（但也要规范化）
            return api_path.rstrip('. \t\n\r')
        else:
            # 如果配置的是路径，拼接基础URL
            # 确保api_path以/开头
            if not api_path.startswith('/'):
                api_path = '/' + api_path
            # 拼接URL
            base_url = self.api_base_url
            if base_url is None:
                raise ValueError("数据库中没有配置 third_party_api_base_url，无法构建API URL。请先在系统配置中设置该参数。")
            return f"{base_url}{api_path}"
    
    def update_session_headers(self):
        """更新会话请求头"""
        self.session.headers.update(self.headers)
    
    @log_api_call
    def get_custom_loan(self, idcard: str) -> Optional[List[CustomerLoan]]:
        """
        获取客户贷款信息
        :param idcard: 身份证号
        :return: CustomerLoan对象列表
        """
        url = self.get_api_url('get_custom_loan')
        params = {'idcard': idcard}
        
        # 更新请求头
        self.update_session_headers()
        
        response_data = self._make_api_request(url, params)
        if not response_data:
            return None
            
        # 提取贷款数据
        loan_data = self._extract_data_from_response(response_data)
        if not loan_data:
            return None
            
        # 转换第三方数据为CustomerLoan对象列表
        customer_loans = self._convert_loan_data_to_objects(loan_data, idcard)
        logger.info(f"成功获取客户贷款信息，共{len(customer_loans)}条记录")
        return customer_loans
    
    @log_api_call
    def get_customer_info(self, idcard: str) -> Optional[Customer]:
        """
        获取客户基本信息
        :param idcard: 身份证号
        :return: Customer对象
        """
        url = self.get_api_url('get_customer_info')
        params = {'idcard': idcard}
        
        # 更新请求头
        self.update_session_headers()
        
        response_data = self._make_api_request(url, params)
        if not response_data:
            return None
            
        # 提取客户信息数据
        customer_data = self._extract_data_from_response(response_data)
        if not customer_data:
            return None
            
        # 转换为本地Customer模型
        customer = self._convert_to_local_format(customer_data)
        return customer
    
    def _make_api_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        发送API请求并获取响应
        :param url: API URL
        :param params: 请求参数
        :return: 响应数据
        """
        try:
            logger.info(f"发送请求 - URL: {url}, 参数: {params}, 超时时间: {self.request_timeout}秒")
            
            response = self.session.get(
                url, 
                params=params, 
                timeout=(10, self.request_timeout)  # (连接超时, 读取超时)
            )
            
            logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.debug(f"响应数据: {response_data}")
                    
                    # 检查响应状态码
                    if isinstance(response_data, dict) and response_data.get('code') != '200':
                        logger.error(f"API返回错误状态码: {response_data.get('code')}")
                        logger.error(f"错误信息: {response_data.get('msg', '')}")
                        return None
                    
                    return response_data
                    
                except ValueError as json_error:
                    logger.error(f"JSON解析失败: {str(json_error)}")
                    logger.error(f"响应内容: {response.text[:200]}...")  # 只记录前200个字符
                    return None
            else:
                logger.error(f"请求失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text[:200]}...")  # 只记录前200个字符
                return None
                
        except requests.exceptions.Timeout as e:
            logger.error(f"请求超时: {url}")
            logger.error(f"超时详情: {str(e)}")
            logger.error(f"提示: 如果服务在Windows上运行，请确保:")
            logger.error(f"  1. 服务监听地址为 0.0.0.0 而不是 127.0.0.1")
            # logger.error(f"  2. Windows防火墙允许端口 {url.split(':')[-1].split('/')[0]} 的入站连接")
            logger.error(f"  3. 从WSL2访问Windows服务，请使用Windows主机的IP地址")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接错误: {url}")
            logger.error(f"连接错误详情: {str(e)}")
            # 解析URL以获取更详细的信息
            try:
                parsed = urlparse(url)
                logger.error(f"URL解析信息:")
                logger.error(f"  协议: {parsed.scheme}")
                logger.error(f"  主机: {parsed.hostname}")
                logger.error(f"  端口: {parsed.port or (443 if parsed.scheme == 'https' else 80)}")
                logger.error(f"  路径: {parsed.path}")
                # 检查IP地址格式
                if parsed.hostname and parsed.hostname.endswith('.'):
                    logger.error(f"  警告: 主机名末尾有点号，已自动清理")
            except Exception as parse_error:
                logger.error(f"URL解析失败: {str(parse_error)}")
            logger.error(f"提示: 如果服务在Windows上运行，请检查:")
            logger.error(f"  1. 服务是否正在运行")
            logger.error(f"  2. 服务监听的IP和端口是否正确（应监听 0.0.0.0 而不是 127.0.0.1）")
            logger.error(f"  3. 从WSL2访问Windows服务，请使用Windows主机的IP地址（如 192.168.3.115）")
            logger.error(f"  4. 或使用WSL2的nameserver IP（通常为 10.255.255.254）")
            logger.error(f"  5. 检查Windows防火墙是否允许该端口的入站连接")
            return None
        except Exception as e:
            logger.error(f"请求异常: {str(e)}", exc_info=True)
            return None
    
    def _extract_data_from_response(self, response_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Any:
        """
        从响应中提取数据
        :param response_data: 响应数据
        :return: 提取的业务数据
        """
        if isinstance(response_data, dict):
            logger.debug(f"响应数据是字典，键: {list(response_data.keys())}")
            
            if 'data' in response_data:
                data = response_data['data']
                logger.debug(f"从data字段提取数据")
                return data
            elif 'result' in response_data:
                return response_data['result']
            else:
                logger.warning(f"响应数据中没有data或result字段，可用字段: {list(response_data.keys())}")
                return None
                
        elif isinstance(response_data, list):
            logger.debug(f"响应数据是列表，包含 {len(response_data)} 条记录")
            return response_data
            
        else:
            logger.warning(f"响应数据类型未知: {type(response_data)}")
            return None
    
    def _convert_to_local_format(self, third_party_data: Dict[str, Any]) -> Customer:
        """
        将第三方客户数据转换为Customer对象
        :param third_party_data: 第三方客户数据
        :return: Customer对象
        """
        logger.debug(f"开始转换客户数据")
        customer_data = {}
        
        # 字段映射表，格式: 本地字段名 -> (第三方字段名, 转换函数)
        field_mappings = {
            'name': ('name', str),
            'customer_type': ('cust_type', str),
            'age': ('age', lambda v: int(v) if v not in [None, ''] else None),
            'cert_id': ('cert_no', str),
            'gender': ('gender', str),
            'is_trusted': ('is_trust_user', str),
            'is_dormant': ('is_sleeper', str),
            'marital_status': ('marital_state', str),
            'education_level': ('highest_education', str),
            'degree': ('education_degree', str),
            'political_status': ('political_face', str),
            'health_status': ('health_state', str),
            'occupation_type': ('occupation_type', str),
            'employer_name': ('work_corp', str),
            'annual_income': ('yearly_income', lambda v: float(v) if v not in [None, ''] else None),
            'working_years': ('yearly_working', lambda v: float(v) if v not in [None, ''] else None),
            'main_income_source': ('MAJR_INCOM_SRC', str),
            'business_model': ('markting_model', str),
            'business_category': ('markting_main_category', str),
            'business_address': ('oprt_assdress', str),
            'main_business': ('biz_main_biz', str),
            'operation_years': ('oprt_year', lambda v: int(v) if v not in [None, ''] else None),
            'rural_entity_type': ('new_rural_oprt_main', str),
            'company_name': ('compamy', str),
            'dependents_count': ('family_num', lambda v: int(v) if v not in [None, ''] else None),
            'family_income_source': ('family_income_source', str),
            'family_annual_income': ('family_yearly_income', lambda v: float(v) if v not in [None, ''] else None),
            'family_annual_expense': ('family_yearly_pay', lambda v: float(v) if v not in [None, ''] else None),
            'family_monthly_income': ('family_month_income', lambda v: float(v) if v not in [None, ''] else None),
            'family_assets': ('family_assets', lambda v: float(v) if v not in [None, ''] else None),
            'family_debt': ('family_scope', lambda v: float(v) if v not in [None, ''] else None),
            'family_net_assets': ('family_purely_asset', lambda v: float(v) if v not in [None, ''] else None),
            'household_address': ('registration_address', str),
            'risk_level': ('risk_level', str),
            'residence_type': ('residence', str),
            'credit_card': ('credit_card', lambda v: v),
            'zhengxin': ('zhengxin', lambda v: v)
        }

        # 特殊处理日期字段
        birth_date = third_party_data.get('birthday')
        if birth_date:
            try:
                customer_data['birth_date'] = datetime.strptime(birth_date, '%Y-%m-%d').date()
            except Exception as e:
                logger.warning(f"birth_date解析失败: {birth_date}, 错误: {e}")
                customer_data['birth_date'] = None
        else:
            customer_data['birth_date'] = None
        
        # 应用字段映射
        for local_field, (remote_field, converter) in field_mappings.items():
            try:
                value = third_party_data.get(remote_field)
                if value is not None:
                    customer_data[local_field] = converter(value)
                else:
                    customer_data[local_field] = None
            except Exception as e:
                logger.warning(f"字段 {local_field} 转换失败: {e}")
                customer_data[local_field] = None
        
        # 设置时间戳
        customer_data['created_at'] = None
        customer_data['updated_at'] = None
        logger.info(f"customer_data: customer_data")
        logger.info(f"Customer(**customer_data): {Customer(**customer_data)}")

        return Customer(**customer_data)
    
    def _convert_loan_data_to_objects(self, loan_data: List[Dict[str, Any]], id_card: str) -> List[CustomerLoan]:
        """
        将第三方贷款数据转换为CustomerLoan对象列表
        :param loan_data: 第三方贷款数据列表
        :param id_card: 身份证号
        :return: CustomerLoan对象列表
        """
        logger.debug(f"开始转换贷款数据 - 输入数据类型: {type(loan_data)}")
        
        customer_loans = []
        
        # 确保loan_data是列表
        if not isinstance(loan_data, list):
            logger.warning(f"贷款数据不是列表格式，尝试转换")
            loan_data = self._ensure_list_format(loan_data)
            if not loan_data:
                return []
        
        logger.info(f"处理 {len(loan_data)} 条贷款记录")
        
        # 日期格式转换函数
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, '%Y%m%d').date()
            except ValueError:
                logger.warning(f"日期转换失败: {date_str}")
                return None
        
        # 字段映射表，格式: 本地字段名 -> (第三方字段名, 默认值, 转换函数)
        field_mappings = {
            'customer_name': ('customer_name', '', str),
            'cert_id': ('cert_id', id_card, str),
            'loan_amount': ('loan_mount', 0, float),
            'balance': ('balance', 0, float),
            'loan_date': ('loan_date', None, parse_date),
            'expir_date': ('expir_date', None, parse_date),
            'clear_date': ('clear_date', None, parse_date),
            'total_prd': ('total_prd', 0, int),
            'leading_rate': ('leading_rate', 0, float),
            'repayment_method': ('repayment_method', '', str),
            'interest_collection_cycle': ('cinterest_collection_cycle', 0, int),
            'business_type': ('bussiness_type', '', str),
            'loan_status': ('loan_status', '', str),
            'product_name': ('product_name', '', str),
        }
        
        for i, loan_item in enumerate(loan_data):
            try:
                customer_loan = CustomerLoan()
                
                # 应用字段映射
                for local_field, (remote_field, default_value, converter) in field_mappings.items():
                    try:
                        value = loan_item.get(remote_field)
                        if value is not None and value != '':
                            setattr(customer_loan, local_field, converter(value))
                        else:
                            setattr(customer_loan, local_field, default_value)
                    except Exception as e:
                        logger.warning(f"字段 {local_field} 转换失败: {e}")
                        setattr(customer_loan, local_field, default_value)
                
                # 设置时间戳
                customer_loan.created_at = datetime.now()
                customer_loan.updated_at = datetime.now()
                
                customer_loans.append(customer_loan)
                
            except Exception as e:
                logger.error(f"转换第 {i+1} 条贷款数据异常: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"转换完成，共创建 {len(customer_loans)} 个贷款对象")
        return customer_loans
    
    def _ensure_list_format(self, data: Any) -> List:
        """确保数据是列表格式"""
        if isinstance(data, list):
            return data
            
        if isinstance(data, dict):
            # 尝试提取列表数据
            for key in ['data', 'result', 'loans', 'list', 'items']:
                if key in data and isinstance(data[key], list):
                    return data[key]
                    
            logger.error(f"无法从字典中提取列表数据，字典键: {list(data.keys())}")
            return []
            
        logger.error(f"数据格式不正确: {type(data)}")
        return []


def get_customer_loan_from_third_party(idcard: str) -> Optional[List[CustomerLoan]]:
    """
    从第三方获取客户贷款信息的便捷方法
    
    使用示例:
    # 根据身份证号获取贷款信息
    customer_loans = get_customer_loan_from_third_party(
        idcard="320821197309154713"
    )
    
    if customer_loans:
        for loan in customer_loans:
            print(f"客户: {loan.customer_name}")
            print(f"贷款金额: {loan.loan_amount}")
            print(f"贷款状态: {loan.loan_status}")
            print(f"产品名称: {loan.product_name}")
    
    :param idcard: 身份证号
    :return: CustomerLoan对象列表
    """
    client = ThirdPartyCustomerClient()
    return client.get_custom_loan(idcard=idcard)


def get_customer_from_third_party(idcard: str) -> Optional[Customer]:
    """
    从第三方获取客户基本信息的便捷方法
    :param idcard: 身份证号
    :return: Customer对象或None
    """
    client = ThirdPartyCustomerClient()
    return client.get_customer_info(idcard=idcard)
