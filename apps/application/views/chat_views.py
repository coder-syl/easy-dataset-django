# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： chat_views.py
    @date：2023/11/14 9:53
    @desc:
"""

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.views import APIView
import logging
import ipaddress
from typing import Dict, Any

from application.serializers.chat_message_serializers import ChatMessageSerializer, OpenAIChatSerializer
from application.serializers.chat_serializers import ChatSerializers, ChatRecordSerializer
from application.swagger_api.chat_api import ChatApi, VoteApi, ChatRecordApi, ImproveApi, ChatRecordImproveApi, \
    ChatClientHistoryApi, OpenAIChatApi
from application.views import get_application_operation_object
from common.auth import TokenAuth, has_permissions, OpenAIKeyAuth
from common.constants.authentication_type import AuthenticationType
from common.constants.permission_constants import Permission, Group, Operate, \
    RoleConstants, ViewPermission, CompareConstants
from common.log.log import log
from common.response import result
from common.util.common import query_params_to_single_dict
from dataset.serializers.file_serializers import FileSerializer
from application.models.business import Customer, Product, CustomerRiskProfile, CustomerLoan  # , InteractionHistory, CustomerPreference
from application.recommendation.recommender import ProductRecommender
from application.services.third_party_customer import get_customer_loan_from_third_party, get_customer_from_third_party
from application.services.scene_service import SceneService
 
logger = logging.getLogger('max_kb')

class Openai(APIView):
    authentication_classes = [OpenAIKeyAuth]

    @action(methods=['POST'], detail=False)
    @swagger_auto_schema(operation_summary=_("OpenAI Interface Dialogue"),
                         operation_id=_("OpenAI Interface Dialogue"),
                         request_body=OpenAIChatApi.get_request_body_api(),
                         responses=OpenAIChatApi.get_response_body_api(),
                         tags=[_("OpenAI Dialogue")])
    def post(self, request: Request, application_id: str):
        return OpenAIChatSerializer(data={'application_id': application_id, 'client_id': request.auth.client_id,
                                          'client_type': request.auth.client_type}).chat(request.data)


class ChatView(APIView):
    authentication_classes = [TokenAuth]

    class Export(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['POST'], detail=False)
        @swagger_auto_schema(operation_summary=_("Export conversation"),
                             operation_id=_("Export conversation"),
                             manual_parameters=ChatApi.get_request_params_api(),
                             tags=[_("Application/Conversation Log")]
                             )
        @has_permissions(
            ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_KEY],
                           [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                           dynamic_tag=keywords.get('application_id'))])
        )
        @log(menu='Conversation Log', operate="Export conversation",
             get_operation_object=lambda r, k: get_application_operation_object(k.get('application_id')))
        def post(self, request: Request, application_id: str):
            return ChatSerializers.Query(
                data={**query_params_to_single_dict(request.query_params), 'application_id': application_id,
                      'user_id': request.user.id}).export(request.data)

    class Open(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['GET'], detail=False)
        @swagger_auto_schema(operation_summary=_("Get the session id according to the application id"),
                             operation_id=_("Get the session id according to the application id"),
                             manual_parameters=ChatApi.OpenChat.get_request_params_api(),
                             tags=[_("Application/Chat")])
        @has_permissions(
            ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_ACCESS_TOKEN,
                            RoleConstants.APPLICATION_KEY],
                           [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                           dynamic_tag=keywords.get('application_id'))],
                           compare=CompareConstants.AND)
        )
        def get(self, request: Request, application_id: str):
            return result.success(ChatSerializers.OpenChat(
                data={'user_id': request.user.id, 'application_id': application_id}).open())

    class OpenWorkFlowTemp(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['POST'], detail=False)
        @swagger_auto_schema(operation_summary=_("Get the workflow temporary session id"),
                             operation_id=_("Get the workflow temporary session id"),
                             request_body=ChatApi.OpenWorkFlowTemp.get_request_body_api(),
                             tags=[_("Application/Chat")])
        def post(self, request: Request):
            return result.success(ChatSerializers.OpenWorkFlowChat(
                data={'user_id': request.user.id, **request.data}).open())

    class OpenTemp(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['POST'], detail=False)
        @swagger_auto_schema(operation_summary=_("Get a temporary session id"),
                             operation_id=_("Get a temporary session id"),
                             request_body=ChatApi.OpenTempChat.get_request_body_api(),
                             tags=[_("Application/Chat")])
        @has_permissions(RoleConstants.ADMIN, RoleConstants.USER)
        def post(self, request: Request):
            return result.success(ChatSerializers.OpenTempChat(
                data={**request.data, 'user_id': request.user.id}).open())

    class Message(APIView):
        authentication_classes = [TokenAuth]

        def get_client_ip(self, request):
            """获取客户端真实IP地址"""
            def is_private_ip(ip_str):
                """检查是否为私有IP地址"""
                try:
                    ip = ipaddress.ip_address(ip_str.strip())
                    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                except (ValueError, AttributeError):
                    return False
            
            def is_docker_internal_ip(ip_str):
                """检查是否为Docker内部IP"""
                docker_networks = [
                    '172.17.', '172.18.', '172.19.', '172.20.',
                    '172.21.', '172.22.', '172.23.', '172.24.',
                    '172.25.', '172.26.', '172.27.', '172.28.',
                    '172.29.', '172.30.', '172.31.',
                    '10.0.', '192.168.', '127.0.', '169.254.'
                ]
                return any(ip_str.startswith(net) for net in docker_networks)
            
            # 按优先级检查各种HTTP头
            ip_headers = [
                'HTTP_X_REAL_IP',           # Nginx等反向代理常用
                'HTTP_X_FORWARDED_FOR',     # 标准代理头
                'HTTP_X_CLIENT_IP',         # 其他代理
                'HTTP_CF_CONNECTING_IP',    # Cloudflare
                'HTTP_X_CLUSTER_CLIENT_IP', # 集群环境
            ]
            
            # 首先检查各个HTTP头
            for header in ip_headers:
                ip_value = request.META.get(header)
                if ip_value:
                    # X-Forwarded-For可能包含多个IP，取第一个
                    ips = [ip.strip() for ip in ip_value.split(',')]
                    for ip in ips:
                        if ip and not is_private_ip(ip) and not is_docker_internal_ip(ip):
                            return ip
                    # 如果没有公网IP，至少返回第一个（可能是代理IP）
                    if ips and ips[0]:
                        return ips[0]
            
            # 最后检查REMOTE_ADDR
            remote_addr = request.META.get('REMOTE_ADDR')
            if remote_addr:
                # 如果是私有IP或Docker内部IP，记录警告但仍然返回
                if is_private_ip(remote_addr) or is_docker_internal_ip(remote_addr):
                    logger.warning(f"获取到内部IP地址: {remote_addr}，可能缺少正确的代理头配置")
                return remote_addr
            
            # 如果都没有，返回未知
            logger.warning("无法获取客户端IP地址")
            return 'unknown'

        @action(methods=['POST'], detail=False)
        @swagger_auto_schema(operation_summary=_("dialogue"),
                             operation_id=_("dialogue"),
                             request_body=ChatApi.get_request_body_api(),
                             tags=[_("Application/Chat")])
        @has_permissions(
            ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_KEY,
                            RoleConstants.APPLICATION_ACCESS_TOKEN],
                           [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                           dynamic_tag=keywords.get('application_id'))])
        )
        def post(self, request: Request, chat_id: str):
            # 获取客户端IP地址
            ip_address = self.get_client_ip(request)
            
            return ChatMessageSerializer(data={'chat_id': chat_id, 'message': request.data.get('message'),
                                               're_chat': (request.data.get(
                                                   're_chat') if 're_chat' in request.data else False),
                                               'stream': (request.data.get(
                                                   'stream') if 'stream' in request.data else True),
                                               'application_id': (request.auth.keywords.get(
                                                   'application_id') if request.auth.client_type == AuthenticationType.APPLICATION_ACCESS_TOKEN.value else None),
                                               'client_id': request.auth.client_id,
                                               'form_data': (request.data.get(
                                                   'form_data') if 'form_data' in request.data else {}),
                                               'image_list': request.data.get(
                                                   'image_list') if 'image_list' in request.data else [],
                                               'document_list': request.data.get(
                                                   'document_list') if 'document_list' in request.data else [],
                                               'audio_list': request.data.get(
                                                   'audio_list') if 'audio_list' in request.data else [],
                                               'other_list': request.data.get(
                                                   'other_list') if 'other_list' in request.data else [],
                                               'type': request.data.get(
                                                   'type') if 'type' in request.data else '通用',
                                               'user_info': request.data.get(
                                                   'user_info') if 'user_info' in request.data else {},
                                               'client_type': request.auth.client_type,
                                               'node_id': request.data.get('node_id', None),
                                               'runtime_node_id': request.data.get('runtime_node_id', None),
                                               'node_data': request.data.get('node_data', {}),
                                               'chat_record_id': request.data.get('chat_record_id'),
                                               'child_node': request.data.get('child_node'),
                                               'ip_address': ip_address}
                                         ).chat()

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_summary=_("Get the conversation list"),
                         operation_id=_("Get the conversation list"),
                         manual_parameters=ChatApi.get_request_params_api(),
                         responses=result.get_api_array_response(ChatApi.get_response_body_api()),
                         tags=[_("Application/Conversation Log")]
                         )
    @has_permissions(
        ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_KEY],
                       [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                       dynamic_tag=keywords.get('application_id'))])
    )
    def get(self, request: Request, application_id: str):
        return result.success(ChatSerializers.Query(
            data={**query_params_to_single_dict(request.query_params), 'application_id': application_id,
                  'user_id': request.user.id}).list())

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['DELETE'], detail=False)
        @swagger_auto_schema(operation_summary=_("Delete a conversation"),
                             operation_id=_("Delete a conversation"),
                             tags=[_("Application/Conversation Log")])
        @has_permissions(ViewPermission(
            [RoleConstants.ADMIN, RoleConstants.USER],
            [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.MANAGE,
                                            dynamic_tag=keywords.get('application_id'))],
            compare=CompareConstants.AND),
            compare=CompareConstants.AND)
        @log(menu='Conversation Log', operate="Delete a conversation",
             get_operation_object=lambda r, k: get_application_operation_object(k.get('application_id')))
        def delete(self, request: Request, application_id: str, chat_id: str):
            return result.success(
                ChatSerializers.Operate(
                    data={'application_id': application_id, 'user_id': request.user.id,
                          'chat_id': chat_id}).delete())

    class ClientChatHistoryPage(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['GET'], detail=False)
        @swagger_auto_schema(operation_summary=_("Get client conversation list by paging"),
                             operation_id=_("Get client conversation list by paging"),
                             manual_parameters=result.get_page_request_params(
                                 ChatClientHistoryApi.get_request_params_api()),
                             responses=result.get_page_api_response(ChatApi.get_response_body_api()),
                             tags=[_("Application/Conversation Log")]
                             )
        @has_permissions(
            ViewPermission([RoleConstants.APPLICATION_ACCESS_TOKEN],
                           [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                           dynamic_tag=keywords.get('application_id'))])
        )
        def get(self, request: Request, application_id: str, current_page: int, page_size: int):
            return result.success(ChatSerializers.ClientChatHistory(
                data={'client_id': request.auth.client_id, 'application_id': application_id}).page(
                current_page=current_page,
                page_size=page_size))

        class Operate(APIView):
            authentication_classes = [TokenAuth]

            @action(methods=['DELETE'], detail=False)
            @swagger_auto_schema(operation_summary=_("Client deletes conversation"),
                                 operation_id=_("Client deletes conversation"),
                                 tags=[_("Application/Conversation Log")])
            @has_permissions(ViewPermission(
                [RoleConstants.APPLICATION_ACCESS_TOKEN],
                [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                dynamic_tag=keywords.get('application_id'))],
                compare=CompareConstants.AND),
                compare=CompareConstants.AND)
            @log(menu='Conversation Log', operate="Client deletes conversation",
                 get_operation_object=lambda r, k: get_application_operation_object(k.get('application_id')))
            def delete(self, request: Request, application_id: str, chat_id: str):
                return result.success(
                    ChatSerializers.Operate(
                        data={'application_id': application_id, 'user_id': request.user.id,
                              'chat_id': chat_id}).logic_delete())

            @action(methods=['PUT'], detail=False)
            @swagger_auto_schema(operation_summary=_("Client modifies dialogue summary"),
                                 operation_id=_("Client modifies dialogue summary"),
                                 request_body=ChatClientHistoryApi.Operate.ReAbstract.get_request_body_api(),
                                 tags=[_("Application/Conversation Log")])
            @has_permissions(ViewPermission(
                [RoleConstants.APPLICATION_ACCESS_TOKEN],
                [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                dynamic_tag=keywords.get('application_id'))],
                compare=CompareConstants.AND),
                compare=CompareConstants.AND)
            @log(menu='Conversation Log', operate="Client modifies dialogue summary",
                 get_operation_object=lambda r, k: get_application_operation_object(k.get('application_id')))
            def put(self, request: Request, application_id: str, chat_id: str):
                return result.success(
                    ChatSerializers.Operate(
                        data={'application_id': application_id, 'user_id': request.user.id,
                              'chat_id': chat_id}).re_abstract(request.data))

    class Page(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['GET'], detail=False)
        @swagger_auto_schema(operation_summary=_("Get the conversation list by page"),
                             operation_id=_("Get the conversation list by page"),
                             manual_parameters=result.get_page_request_params(ChatApi.get_request_params_api()),
                             responses=result.get_page_api_response(ChatApi.get_response_body_api()),
                             tags=[_("Application/Conversation Log")]
                             )
        @has_permissions(
            ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_KEY],
                           [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                           dynamic_tag=keywords.get('application_id'))])
        )
        def get(self, request: Request, application_id: str, current_page: int, page_size: int):
            return result.success(ChatSerializers.Query(
                data={**query_params_to_single_dict(request.query_params), 'application_id': application_id,
                      'user_id': request.user.id}).page(current_page=current_page,
                                                        page_size=page_size))

    class ChatRecord(APIView):
        authentication_classes = [TokenAuth]

        class Operate(APIView):
            authentication_classes = [TokenAuth]

            @action(methods=['GET'], detail=False)
            @swagger_auto_schema(operation_summary=_("Get conversation record details"),
                                 operation_id=_("Get conversation record details"),
                                 manual_parameters=ChatRecordApi.get_request_params_api(),
                                 responses=result.get_api_array_response(ChatRecordApi.get_response_body_api()),
                                 tags=[_("Application/Conversation Log")]
                                 )
            @has_permissions(
                ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_KEY,
                                RoleConstants.APPLICATION_ACCESS_TOKEN],
                               [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                               dynamic_tag=keywords.get('application_id'))])
            )
            def get(self, request: Request, application_id: str, chat_id: str, chat_record_id: str):
                return result.success(ChatRecordSerializer.Operate(
                    data={'application_id': application_id,
                          'chat_id': chat_id,
                          'chat_record_id': chat_record_id}).one(request.auth.current_role))

        @action(methods=['GET'], detail=False)
        @swagger_auto_schema(operation_summary=_("Get a list of conversation records"),
                             operation_id=_("Get a list of conversation records"),
                             manual_parameters=ChatRecordApi.get_request_params_api(),
                             responses=result.get_api_array_response(ChatRecordApi.get_response_body_api()),
                             tags=[_("Application/Conversation Log")]
                             )
        @has_permissions(
            ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_KEY],
                           [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                           dynamic_tag=keywords.get('application_id'))])
        )
        def get(self, request: Request, application_id: str, chat_id: str):
            return result.success(ChatRecordSerializer.Query(
                data={'application_id': application_id,
                      'chat_id': chat_id, 'order_asc': request.query_params.get('order_asc')}).list())

        class Page(APIView):
            authentication_classes = [TokenAuth]

            @action(methods=['GET'], detail=False)
            @swagger_auto_schema(operation_summary=_("Get the conversation history list by page"),
                                 operation_id=_("Get the conversation history list by page"),
                                 manual_parameters=result.get_page_request_params(
                                     ChatRecordApi.get_request_params_api()),
                                 responses=result.get_page_api_response(ChatRecordApi.get_response_body_api()),
                                 tags=[_("Application/Conversation Log")]
                                 )
            @has_permissions(
                ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_KEY],
                               [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                               dynamic_tag=keywords.get('application_id'))])
            )
            def get(self, request: Request, application_id: str, chat_id: str, current_page: int, page_size: int):
                return result.success(ChatRecordSerializer.Query(
                    data={'application_id': application_id,
                          'chat_id': chat_id, 'order_asc': request.query_params.get('order_asc')}).page(current_page,
                                                                                                        page_size))

        class Vote(APIView):
            authentication_classes = [TokenAuth]

            @action(methods=['PUT'], detail=False)
            @swagger_auto_schema(operation_summary=_("Like, Dislike"),
                                 operation_id=_("Like, Dislike"),
                                 manual_parameters=VoteApi.get_request_params_api(),
                                 request_body=VoteApi.get_request_body_api(),
                                 responses=result.get_default_response(),
                                 tags=[_("Application/Chat")]
                                 )
            @has_permissions(
                ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_KEY,
                                RoleConstants.APPLICATION_ACCESS_TOKEN],
                               [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                               dynamic_tag=keywords.get('application_id'))])
            )
            @log(menu='Conversation Log', operate="Like, Dislike",
                 get_operation_object=lambda r, k: get_application_operation_object(k.get('application_id')))
            def put(self, request: Request, application_id: str, chat_id: str, chat_record_id: str):
                return result.success(ChatRecordSerializer.Vote(
                    data={'vote_status': request.data.get('vote_status'), 'chat_id': chat_id,
                          'chat_record_id': chat_record_id}).vote())

        class ChatRecordImprove(APIView):
            authentication_classes = [TokenAuth]

            @action(methods=['GET'], detail=False)
            @swagger_auto_schema(operation_summary=_("Get the list of marked paragraphs"),
                                 operation_id=_("Get the list of marked paragraphs"),
                                 manual_parameters=ChatRecordImproveApi.get_request_params_api(),
                                 responses=result.get_api_response(ChatRecordImproveApi.get_response_body_api()),
                                 tags=[_("Application/Conversation Log/Annotation")]
                                 )
            @has_permissions(
                ViewPermission([RoleConstants.ADMIN, RoleConstants.USER],
                               [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                               dynamic_tag=keywords.get('application_id'))]
                               ))
            def get(self, request: Request, application_id: str, chat_id: str, chat_record_id: str):
                return result.success(ChatRecordSerializer.ChatRecordImprove(
                    data={'chat_id': chat_id, 'chat_record_id': chat_record_id}).get())

        class Improve(APIView):
            authentication_classes = [TokenAuth]

            @action(methods=['PUT'], detail=False)
            @swagger_auto_schema(operation_summary=_("Annotation"),
                                 operation_id=_("Annotation"),
                                 manual_parameters=ImproveApi.get_request_params_api(),
                                 request_body=ImproveApi.get_request_body_api(),
                                 responses=result.get_api_response(ChatRecordApi.get_response_body_api()),
                                 tags=[_("Application/Conversation Log/Annotation")]
                                 )
            @has_permissions(
                ViewPermission([RoleConstants.ADMIN, RoleConstants.USER],
                               [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                               dynamic_tag=keywords.get('application_id'))],

                               ), ViewPermission([RoleConstants.ADMIN, RoleConstants.USER],
                                                 [lambda r, keywords: Permission(group=Group.DATASET,
                                                                                 operate=Operate.MANAGE,
                                                                                 dynamic_tag=keywords.get(
                                                                                     'dataset_id'))],
                                                 compare=CompareConstants.AND
                                                 ), compare=CompareConstants.AND)
            @log(menu='Conversation Log', operate="Annotation",
                 get_operation_object=lambda r, k: get_application_operation_object(k.get('application_id')))
            def put(self, request: Request, application_id: str, chat_id: str, chat_record_id: str, dataset_id: str,
                    document_id: str):
                return result.success(ChatRecordSerializer.Improve(
                    data={'chat_id': chat_id, 'chat_record_id': chat_record_id,
                          'dataset_id': dataset_id, 'document_id': document_id}).improve(request.data))

            @action(methods=['POST'], detail=False)
            @swagger_auto_schema(operation_summary=_("Add to Knowledge Base"),
                                 operation_id=_("Add to Knowledge Base"),
                                 manual_parameters=ImproveApi.get_request_params_api_post(),
                                 request_body=ImproveApi.get_request_body_api_post(),
                                 tags=[_("Application/Conversation Log/Add to Knowledge Base")]
                                 )
            @has_permissions(
                ViewPermission([RoleConstants.ADMIN, RoleConstants.USER],
                               [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                               dynamic_tag=keywords.get('application_id'))],

                               ), ViewPermission([RoleConstants.ADMIN, RoleConstants.USER],
                                                 [lambda r, keywords: Permission(group=Group.DATASET,
                                                                                 operate=Operate.MANAGE,
                                                                                 dynamic_tag=keywords.get(
                                                                                     'dataset_id'))],
                                                 compare=CompareConstants.AND
                                                 ), compare=CompareConstants.AND)
            @log(menu='Conversation Log', operate="Add to Knowledge Base",
                 get_operation_object=lambda r, k: get_application_operation_object(k.get('application_id')))
            def post(self, request: Request, application_id: str, dataset_id: str):
                return result.success(ChatRecordSerializer.PostImprove().post_improve(request.data))

            class Operate(APIView):
                authentication_classes = [TokenAuth]

                @action(methods=['DELETE'], detail=False)
                @swagger_auto_schema(operation_summary=_("Delete a Annotation"),
                                     operation_id=_("Delete a Annotation"),
                                     manual_parameters=ImproveApi.get_request_params_api(),
                                     responses=result.get_api_response(ChatRecordApi.get_response_body_api()),
                                     tags=[_("Application/Conversation Log/Annotation")]
                                     )
                @has_permissions(
                    ViewPermission([RoleConstants.ADMIN, RoleConstants.USER],
                                   [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                                   dynamic_tag=keywords.get('application_id'))],

                                   ), ViewPermission([RoleConstants.ADMIN, RoleConstants.USER],
                                                     [lambda r, keywords: Permission(group=Group.DATASET,
                                                                                     operate=Operate.MANAGE,
                                                                                     dynamic_tag=keywords.get(
                                                                                         'dataset_id'))],
                                                     compare=CompareConstants.AND
                                                     ), compare=CompareConstants.AND)
                @log(menu='Conversation Log', operate="Delete a Annotation",
                     get_operation_object=lambda r, k: get_application_operation_object(k.get('application_id')))
                def delete(self, request: Request, application_id: str, chat_id: str, chat_record_id: str,
                           dataset_id: str,
                           document_id: str, paragraph_id: str):
                    return result.success(ChatRecordSerializer.Improve.Operate(
                        data={'chat_id': chat_id, 'chat_record_id': chat_record_id,
                              'dataset_id': dataset_id, 'document_id': document_id,
                              'paragraph_id': paragraph_id}).delete())

    class UploadFile(APIView):
        authentication_classes = [TokenAuth]
        parser_classes = [MultiPartParser]

        @action(methods=['POST'], detail=False)
        @swagger_auto_schema(operation_summary=_("Upload files"),
                             operation_id=_("Upload files"),
                             manual_parameters=[
                                 openapi.Parameter(name='application_id',
                                                   in_=openapi.IN_PATH,
                                                   type=openapi.TYPE_STRING,
                                                   required=True,
                                                   description=_('Application ID')),
                                 openapi.Parameter(name='chat_id',
                                                   in_=openapi.IN_PATH,
                                                   type=openapi.TYPE_STRING,
                                                   required=True,
                                                   description=_('Conversation ID')),
                                 openapi.Parameter(name='file',
                                                   in_=openapi.IN_FORM,
                                                   type=openapi.TYPE_FILE,
                                                   required=True,
                                                   description=_('Upload file'))
                             ],
                             tags=[_("Application/Conversation Log")]
                             )
        @has_permissions(
            ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_KEY,
                            RoleConstants.APPLICATION_ACCESS_TOKEN],
                           [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                           dynamic_tag=keywords.get('application_id'))])
        )
        def post(self, request: Request, application_id: str, chat_id: str):
            files = request.FILES.getlist('file')
            file_ids = []
            debug = request.data.get("debug", "false").lower() == "true"
            meta = {'application_id': application_id, 'chat_id': chat_id, 'debug': debug}
            for file in files:
                file_url = FileSerializer(data={'file': file, 'meta': meta}).upload()
                file_ids.append({'name': file.name, 'url': file_url, 'file_id': file_url.split('/')[-1]})
            return result.success(file_ids)

    class Recommend(APIView):
        authentication_classes = [TokenAuth]

        @action(methods=['GET'], detail=False)
        @swagger_auto_schema(operation_summary=_('Get user info and recommended products'),
                             operation_id=_('Get user info and recommended products'),
                             tags=[_('Application/Recommend')])
        @has_permissions(
            ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_ACCESS_TOKEN],
                           [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                           dynamic_tag=keywords.get('application_id'))])
        )
        def get(self, request: Request, application_id: str):
            customer_id = request.query_params.get('customer_id')
            scene_type = request.query_params.get('scene_type', '通用')  # 获取场景类型，默认为"通用"
            logger.info(f'获取推荐请求 - 客户ID: {customer_id}, 场景类型: {scene_type}')
            
            user_info = {}
            scene_result = {}  # 场景接口返回结果
            
            if not customer_id:
                logger.warning(f"应用 {application_id}: 请求中未提供客户ID")
                return result.success({
                    "userInfo": user_info, 
                    "sceneResult": scene_result
                })
            
            try:
                # 获取客户信息
                customer = get_customer_from_third_party(customer_id)
                logger.info(f'客户信息获取成功 - 客户ID: {customer_id}')
                if customer is None:
                    logger.error(f"无法获取客户信息 - 客户ID: {customer_id}")
                    return result.error(f"无法获取客户信息，客户ID: {customer_id}")
           
                logger.info(f'客户基本信息 - 姓名: {customer.name}, 身份证号: {customer.cert_id}')
                
                # 获取客户风险画像
                customer_risk_profile = None
                try:
                    customer_risk_profile = CustomerRiskProfile.objects.get(customer=customer)
                except CustomerRiskProfile.MultipleObjectsReturned:
                    logger.warning(f"客户 {customer_id}: 发现多条风险画像记录，使用第一条")
                    customer_risk_profile = CustomerRiskProfile.objects.filter(customer=customer).first()
                except CustomerRiskProfile.DoesNotExist:
                    logger.info(f"客户 {customer_id}: 未找到风险画像")
                
                # 获取客户偏好（已注释，待实现）
                customer_preferences = None
                # try:
                #     customer_preferences = CustomerPreference.objects.get(customer=customer)
                # except CustomerPreference.DoesNotExist:
                #     logger.info(f"客户 {customer_id}: 未找到客户偏好")
                
                # 获取客户贷款历史
                logger.info(f"开始获取客户贷款历史 - 客户ID: {customer_id}, 身份证号: {customer.cert_id}")
                customer_loans = get_customer_loan_from_third_party(customer_id)
                logger.info(f"客户贷款历史查询完成 - 客户ID: {customer_id}, 共找到 {len(customer_loans) if customer_loans else 0} 条记录")
                
                # 如果贷款历史为空，记录详细信息
                if not customer_loans:
                    logger.warning(f"客户 {customer_id} 的贷款历史为空，可能的原因:")
                    logger.warning(f"  1. 第三方API未返回数据")
                    logger.warning(f"  2. 身份证号 {customer.cert_id} 在第三方系统中不存在")
                    logger.warning(f"  3. 第三方API连接失败")
                    logger.warning(f"  4. 第三方API返回的数据格式不正确")
                else:
                    logger.info(f"客户 {customer_id} 贷款历史详情:")
                    for i, loan in enumerate(customer_loans, 1):
                        logger.info(f"  贷款记录 {i}: 客户姓名={loan.customer_name}, 产品名称={loan.product_name}, 贷款金额={loan.loan_amount}, 贷款状态={loan.loan_status}")
                
                # 构建用户信息
                user_info = self._build_user_info(customer, customer_risk_profile, customer_preferences, customer_loans)
                
                # 根据场景类型调用不同的场景接口
                try:
                    logger.info(f"开始调用场景接口 - 场景类型: {scene_type}, 客户ID: {customer_id}")
                    scene_result = SceneService.call_scene_api(scene_type, user_info, list(customer_loans) if customer_loans else [])
                    logger.info(f"场景接口调用完成 - 场景类型: {scene_type}, 返回结果: {scene_result}")
                except Exception as e:
                    logger.error(f"场景接口调用异常 - 场景类型: {scene_type}, 错误信息: {str(e)}", exc_info=True)
                    scene_result = {
                        'status': 'error',
                        'message': f'场景接口调用异常: {str(e)}',
                        'data': {}
                    }
                
            except Customer.DoesNotExist:
                logger.error(f"客户不存在 - 客户ID: {customer_id}")
                return result.error(f"客户不存在，客户ID: {customer_id}")
            except Exception as e:
                logger.error(f"获取推荐信息时发生异常 - 客户ID: {customer_id}, 错误信息: {str(e)}", exc_info=True)
                return result.error(f"获取推荐信息时发生异常: {str(e)}")
            
            return result.success({
                "userInfo": user_info, 
                "sceneResult": scene_result  # 场景接口返回结果
            })

        def _build_user_info(self, customer, customer_risk_profile, customer_preferences, customer_loans):
            """构建用户信息字典"""
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
                    "credit_card": customer.credit_card, # 贷记卡信息
                    "zhengxin": customer.zhengxin,
                    "created_at": customer.created_at.isoformat() if customer.created_at else None,
                    "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,

                    # 风险画像（已注释）
                    # "risk_profile": {
                    #     "risk_level": customer_risk_profile.risk_level if customer_risk_profile else None,
                    #     "credit_score": float(customer_risk_profile.credit_score) if customer_risk_profile and customer_risk_profile.credit_score else None,
                    #     "credit_rating": customer_risk_profile.credit_rating if customer_risk_profile else None,
                    #     "credit_record": customer_risk_profile.credit_record if customer_risk_profile else None,
                    #     "default_history": customer_risk_profile.default_history if customer_risk_profile else None,
                    #     "debt_ratio": float(customer_risk_profile.debt_ratio) if customer_risk_profile and customer_risk_profile.debt_ratio else None,
                    #     "payment_capability": float(customer_risk_profile.payment_capability) if customer_risk_profile and customer_risk_profile.payment_capability else None,
                    #     "warning_level": customer_risk_profile.warning_level if customer_risk_profile else None,
                    # } if customer_risk_profile else None,

                    # 客户偏好（已注释）
                    # "preference": {
                    #     "preferred_term_months": customer_preferences.preferred_term_months if customer_preferences else None,
                    #     "preferred_amount": float(customer_preferences.preferred_amount) if customer_preferences and customer_preferences.preferred_amount else None,
                    #     "risk_tolerance": customer_preferences.risk_tolerance if customer_preferences else None,
                    #     "online_preference": customer_preferences.online_preference if customer_preferences else None,
                    # } if customer_preferences else None,

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
                            "customer_name": loan.customer_name,
                            "cert_id": loan.cert_id,
                            "total_prd": loan.total_prd,
                            "clear_date": loan.clear_date.isoformat() if loan.clear_date else None,
                            "repayment_method": loan.repayment_method,
                            "interest_collection_cycle": loan.interest_collection_cycle,
                            "created_at": loan.created_at.isoformat() if loan.created_at else None,
                            "updated_at": loan.updated_at.isoformat() if loan.updated_at else None,
                        }
                        for loan in customer_loans or []
                    ],
                }
            except Exception as e:
                logger.error(f"构建用户信息时发生异常 - 客户ID: {customer.id}, 错误信息: {str(e)}", exc_info=True)
                # 返回基本信息
                return {
                    "id": customer.id,
                    "name": customer.name,
                    "error": f"部分信息获取失败: {str(e)}"
                }

        @action(methods=['POST'], detail=False)
        @swagger_auto_schema(operation_summary=_('Get detailed product recommendations'),
                             operation_id=_('Get detailed product recommendations'),
                             request_body=openapi.Schema(
                                 type=openapi.TYPE_OBJECT,
                                 properties={
                                     'customer_id': openapi.Schema(type=openapi.TYPE_STRING, description='Customer ID'),
                                     'top_n': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of recommendations', default=5),
                                     'product_types': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description='Filter by product types'),
                                     'min_amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Minimum loan amount'),
                                     'max_amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Maximum loan amount'),
                                     'risk_level': openapi.Schema(type=openapi.TYPE_STRING, description='Risk level filter'),
                                 },
                                 required=['customer_id']
                             ),
                             tags=[_('Application/Recommend')])
        @has_permissions(
            ViewPermission([RoleConstants.ADMIN, RoleConstants.USER, RoleConstants.APPLICATION_ACCESS_TOKEN],
                           [lambda r, keywords: Permission(group=Group.APPLICATION, operate=Operate.USE,
                                                           dynamic_tag=keywords.get('application_id'))])
        )
        def post(self, request: Request, application_id: str):
            """获取详细的产品推荐"""
            try:
                customer_id = request.data.get('customer_id')
                top_n = request.data.get('top_n', 5)
                product_types = request.data.get('product_types', [])
                min_amount = request.data.get('min_amount')
                max_amount = request.data.get('max_amount')
                risk_level = request.data.get('risk_level')
                
                logger.info(f"POST推荐请求 - 客户ID: {customer_id}, 筛选条件: 产品类型={product_types}, 金额范围={min_amount}-{max_amount}, 风险等级={risk_level}")
                
                if not customer_id:
                    logger.warning("POST推荐请求缺少客户ID")
                    return result.error("客户ID不能为空")
                
                # 获取客户信息
                try:
                    customer = get_customer_from_third_party(customer_id)
                    if customer is None:
                        logger.error(f"无法获取客户信息 - 客户ID: {customer_id}")
                        return result.fail(msg=f"无法获取客户信息，客户ID: {customer_id}")
                    logger.info(f"找到客户信息 - 客户姓名: {customer.name}")
                except Customer.DoesNotExist:
                    logger.error(f"客户不存在 - 客户ID: {customer_id}")
                    return result.error("客户不存在")
                
                # 获取客户相关数据
                customer_risk_profile = None
                try:
                    customer_risk_profile = CustomerRiskProfile.objects.get(customer=customer)
                except CustomerRiskProfile.MultipleObjectsReturned:
                    logger.warning(f"客户 {customer_id}: 发现多条风险画像记录，使用第一条")
                    customer_risk_profile = CustomerRiskProfile.objects.filter(customer=customer).first()
                except CustomerRiskProfile.DoesNotExist:
                    logger.info(f"客户 {customer_id}: 未找到风险画像")
                
                # 获取客户偏好（已注释，待实现）
                customer_preferences = None
                # try:
                #     customer_preferences = CustomerPreference.objects.get(customer=customer)
                # except CustomerPreference.DoesNotExist:
                #     logger.info(f"客户 {customer_id}: 未找到客户偏好")
                
                customer_loans = CustomerLoan.objects.filter(customer=customer)
                # interaction_history = InteractionHistory.objects.filter(customer=customer)  # 交互历史（已注释）
                
                # 构建产品查询
                products_query = Product.objects.all()
                
                # 应用过滤器
                if product_types:
                    products_query = products_query.filter(product_type__in=product_types)
                    logger.info(f"按产品类型筛选: {product_types}")
                if min_amount is not None:
                    products_query = products_query.filter(max_amount__gte=min_amount)
                    logger.info(f"按最小金额筛选: {min_amount}")
                if max_amount is not None:
                    products_query = products_query.filter(min_amount__lte=max_amount)
                    logger.info(f"按最大金额筛选: {max_amount}")
                if risk_level:
                    products_query = products_query.filter(risk_level=risk_level)
                    logger.info(f"按风险等级筛选: {risk_level}")
                
                products = list(products_query)
                
                if not products:
                    logger.warning("未找到符合筛选条件的产品")
                    return result.success({
                        "status": "success",
                        "message": "未找到符合条件的产品",
                        "recommendations": [],
                        "statistics": {}
                    })
                
                logger.info(f"找到 {len(products)} 个符合筛选条件的产品")
                
                # 使用推荐系统
                try:
                    recommender = ProductRecommender()
                    recommendation_result = recommender.recommend_products(
                        customer=customer,
                        products=products,
                        customer_risk_profile=customer_risk_profile,
                        customer_preferences=customer_preferences,
                        # interaction_history=list(interaction_history),
                        customer_loans=list(customer_loans),
                        top_n=top_n
                    )
                    logger.info(f"推荐系统完成 - 状态: {recommendation_result.get('status')}")
                except Exception as recommender_error:
                    logger.error(f"推荐系统异常 - 错误信息: {str(recommender_error)}", exc_info=True)
                    return result.error(f"推荐系统异常: {str(recommender_error)}")
                
                # 构建详细响应
                response_data = {
                    "status": recommendation_result.get("status", "error"),
                    "message": recommendation_result.get("reason", "推荐成功"),
                    "customer_info": {
                        "id": customer.id,
                        "name": customer.name,
                        "age": customer.age,
                        "income": float(customer.annual_income)/12 if customer.annual_income else 0,
                        "occupation": customer.occupation_type,
                        "company_type": customer.employer_name,
                        "risk_level": customer_risk_profile.risk_level if customer_risk_profile else "medium",
                        "credit_score": float(customer_risk_profile.credit_score) if customer_risk_profile and customer_risk_profile.credit_score else 0,
                    },
                    "recommendations": recommendation_result.get("recommendations", []),
                    "statistics": recommendation_result.get("statistics", {}),
                    "filters_applied": {
                        "product_types": product_types,
                        "min_amount": min_amount,
                        "max_amount": max_amount,
                        "risk_level": risk_level,
                        "top_n": top_n
                    }
                }
                
                logger.info(f"POST推荐请求完成 - 客户ID: {customer_id}")
                return result.success(response_data)
                
            except Exception as e:
                logger.error(f"POST推荐请求异常 - 错误信息: {str(e)}", exc_info=True)
                return result.error(f"推荐系统异常: {str(e)}")
