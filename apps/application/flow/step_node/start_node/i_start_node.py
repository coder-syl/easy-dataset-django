# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： i_start_node.py
    @date：2024/6/3 16:54
    @desc:
"""

from application.flow.i_step_node import INode, NodeResult


class IStarNode(INode):
    type = 'start-node'

    def _run(self):
        # 添加调试日志
        print(f"Start node _run - flow_params_serializer.data: {self.flow_params_serializer.data}")
        return self.execute(**self.flow_params_serializer.data)

    def execute(self, question, type=None, user_info=None, **kwargs) -> NodeResult:
        pass
