"""
标签管理视图
"""
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.db.models import Q

from projects.models import Project
from .models import Tag
from questions.models import Question
from common.response.result import success, error


def get_all_labels_for_tag(tag_id, project):
    """获取某个标签及其所有子标签的 label"""
    labels = []
    queue = [tag_id]
    
    while queue:
        current_id = queue.pop(0)
        try:
            tag = Tag.objects.get(id=current_id, project=project)
            labels.append(tag.label)
            # 获取子标签的 ID，加入队列
            children = Tag.objects.filter(parent_id=current_id, project=project).values_list('id', flat=True)
            queue.extend(list(children))
        except Tag.DoesNotExist:
            continue
    
    return labels


def build_tag_tree(tags, parent_id=None, project=None):
    """构建标签树，并统计问题数量（与 Node.js 的 getTagsTreeWithQuestionCount 保持一致）"""
    tree = []
    for tag in tags:
        if tag.parent_id == parent_id:
            # 递归构建子节点
            children = build_tag_tree(tags, tag.id, project)
            
            # 获取当前标签及其所有子标签的 label
            all_labels = get_all_labels_for_tag(tag.id, project)
            
            # 统计当前标签及其子标签的问题数量（与 Node.js 逻辑一致）
            question_count = Question.objects.filter(
                project=project,
                label__in=all_labels
            ).count()
            
            tag_data = {
                'id': tag.id,
                'label': tag.label,
                'parentId': tag.parent_id,
                'questionCount': question_count  # 添加问题数量统计
            }
            if children:
                tag_data['child'] = children  # 使用 'child' 与 Node.js 保持一致
            tree.append(tag_data)
    return tree


@swagger_auto_schema(
    method='get',
    operation_summary='获取标签树',
    responses={200: openapi.Response('标签树')}
)
@swagger_auto_schema(
    method='post',
    operation_summary='根据标签名获取问题',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'tagName': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: openapi.Response('问题列表')}
)
@swagger_auto_schema(
    method='put',
    operation_summary='创建或更新标签',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'tags': openapi.Schema(type=openapi.TYPE_OBJECT)
        }
    ),
    responses={200: openapi.Response('标签')}
)
@swagger_auto_schema(
    method='delete',
    operation_summary='删除标签',
    responses={200: openapi.Response('删除成功')}
)
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def tag_tree(request, project_id):
    """标签树管理"""
    try:
        project = get_object_or_404(Project, id=project_id)
    except Exception as e:
        return error(message='项目不存在', response_status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            tags = Tag.objects.filter(project=project)
            tag_tree_data = build_tag_tree(list(tags), parent_id=None, project=project)
            return success(data={'tags': tag_tree_data})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            tag_name = request.data.get('tagName')
            if not tag_name:
                return error(message='标签名不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            # 获取该标签下的所有问题
            questions = Question.objects.filter(
                project=project,
                label=tag_name
            )
            
            questions_data = [{
                'id': q.id,
                'question': q.question,
                'label': q.label
            } for q in questions]
            
            return success(data=questions_data)
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            tags_data = request.data.get('tags', {})
            
            if tags_data.get('id') is None or tags_data.get('id') == '':
                # 创建新标签
                tag = Tag.objects.create(
                    project=project,
                    label=tags_data.get('label'),
                    parent_id=tags_data.get('parentId')
                )
                return success(data={'tags': {
                    'id': tag.id,
                    'label': tag.label,
                    'parentId': tag.parent_id
                }})
            else:
                # 更新标签
                tag = get_object_or_404(Tag, id=tags_data.get('id'), project=project)
                tag.label = tags_data.get('label', tag.label)
                tag.save()
                return success(data={'tags': {
                    'id': tag.id,
                    'label': tag.label,
                    'parentId': tag.parent_id
                }})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            tag_id = request.GET.get('id')
            
            if not tag_id:
                return error(message='标签ID不能为空', response_status=status.HTTP_400_BAD_REQUEST)
            
            tag = get_object_or_404(Tag, id=tag_id, project=project)
            tag.delete()
            
            return success(data={'success': True, 'message': '删除标签成功'})
        except Exception as e:
            return error(message=str(e), response_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
