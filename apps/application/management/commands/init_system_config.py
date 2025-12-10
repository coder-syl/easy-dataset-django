# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： init_system_config.py
    @date：2024/12/19 16:00
    @desc: 初始化系统配置管理命令
"""

from django.core.management.base import BaseCommand
from application.models.config import set_config


class Command(BaseCommand):
    help = '初始化系统配置'

    def handle(self, *args, **options):
        """执行初始化"""
        self.stdout.write('开始初始化系统配置...')
        
        # 默认配置项 - 只保留第三方API相关配置
        default_configs = [
            # 第三方API基础配置
            {
                'key': 'third_party_api_base_url',
                'value': 'http://127.0.0.1:4523/m1/6825009-6538994-default',
                'description': '第三方API基础URL'
            },
            {
                'key': 'third_party_request_timeout',
                'value': 30,
                'description': '第三方API请求超时时间（秒）'
            },
            {
                'key': 'third_party_headers',
                'value': {'Content-Type': 'application/json'},
                'description': '第三方API请求头'
            },
            
            # 第三方API接口URL配置
            {
                'key': 'third_party_api_url_get_custom_loan',
                'value': '/restcloud/aiapiapplicatio/getCustomLoan',
                'description': '获取客户贷款信息接口URL'
            },
            {
                'key': 'third_party_api_url_get_customer_info',
                'value': '/restcloud/aiapiapplicatio/getCustomInfo',
                'description': '获取客户基本信息接口URL'
            }
        ]
        
        success_count = 0
        error_count = 0
        
        for config in default_configs:
            try:
                success = set_config(
                    key=config['key'],
                    value=config['value'],
                    description=config['description']
                )
                
                if success:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 配置 {config["key"]} 初始化成功')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ 配置 {config["key"]} 初始化失败')
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ 配置 {config["key"]} 初始化异常: {str(e)}')
                )
        
        self.stdout.write('')
        self.stdout.write(f'初始化完成: 成功 {success_count} 项, 失败 {error_count} 项')
        
        if error_count == 0:
            self.stdout.write(
                self.style.SUCCESS('所有配置初始化成功！')
            )
        else:
            self.stdout.write(
                self.style.WARNING('部分配置初始化失败，请检查日志')
            )
        
        # 显示配置分类统计
        self.stdout.write('')
        self.stdout.write('配置分类统计:')
        categories = {
            '第三方API基础配置': ['third_party_api_base_url', 'third_party_request_timeout', 'third_party_headers'],
            '第三方API接口URL配置': ['third_party_api_url_get_custom_loan', 'third_party_api_url_get_customer_info']
        }
        
        for category, keys in categories.items():
            count = len(keys)
            self.stdout.write(f'  {category}: {count} 项') 