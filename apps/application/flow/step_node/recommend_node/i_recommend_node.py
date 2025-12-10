# coding=utf-8

from typing import Type

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from application.flow.i_step_node import INode, NodeResult
from common.util.field_message import ErrMessage


class RecommendNodeSerializer(serializers.Serializer):
    customer_id = serializers.ListField(required=True, error_messages=ErrMessage.list(_("Customer ID")))


class IRecommendNode(INode):
    type = 'recommend-node'

    def get_node_params_serializer_class(self) -> Type[serializers.Serializer]:
        return RecommendNodeSerializer

    def _run(self):
        customer_id = self.workflow_manage.get_reference_field(
            self.node_params_serializer.data.get('customer_id')[0],
            self.node_params_serializer.data.get('customer_id')[1:])
        return self.execute(customer_id=customer_id, **self.flow_params_serializer.data)

    def execute(self, customer_id, **kwargs) -> NodeResult:
        pass