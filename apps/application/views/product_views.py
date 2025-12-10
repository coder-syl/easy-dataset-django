# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： product_views.py
    @date：2024/12/19 10:00
    @desc: 产品管理相关视图
"""

from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.views import APIView

from application.models.business import Product
from application.serializers.product_serializers import ProductSerializer, ProductQuerySerializer
from common.auth import TokenAuth, has_permissions
from common.constants.permission_constants import Permission, Group, Operate, RoleConstants, ViewPermission
from common.response import result
from common.response.result import Page
from common.util.common import query_params_to_single_dict


class ProductView(APIView):
    authentication_classes = [TokenAuth]

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_summary=_("Get product list"),
                         operation_id=_("Get product list"),
                         tags=[_("Product")],
                         manual_parameters=[
                             openapi.Parameter(name='name', in_=openapi.IN_QUERY, type=openapi.TYPE_STRING,
                                             description='产品名称'),
                             openapi.Parameter(name='category', in_=openapi.IN_QUERY, type=openapi.TYPE_STRING,
                                             description='产品分类'),
                             openapi.Parameter(name='status', in_=openapi.IN_QUERY, type=openapi.TYPE_STRING,
                                             description='产品状态'),
                         ])
    @has_permissions(
        ViewPermission([RoleConstants.ADMIN, RoleConstants.USER],
                       [Permission(group=Group.APPLICATION, operate=Operate.USE)])
    )
    def get(self, request: Request):
        """获取产品列表"""
        try:
            query_params = query_params_to_single_dict(request.query_params)
            name = query_params.get('name', '')
            category = query_params.get('category', '')
            status = query_params.get('status', '')

            # 构建查询条件
            query = Q()
            if name:
                query &= Q(product_name__icontains=name)
            if category:
                query &= Q(product_type__icontains=category)
            # 注意：Product模型中没有status字段，这里先忽略status过滤

            products = Product.objects.filter(query).order_by('-created_at')
            serializer = ProductSerializer(products, many=True)
            
            return result.success(serializer.data)
        except Exception as e:
            return result.error(f"获取产品列表失败: {str(e)}")

    @action(methods=['POST'], detail=False)
    @swagger_auto_schema(operation_summary=_("Create product"),
                         operation_id=_("Create product"),
                         tags=[_("Product")],
                         request_body=ProductSerializer)
    @has_permissions(
        ViewPermission([RoleConstants.ADMIN],
                       [Permission(group=Group.APPLICATION, operate=Operate.MANAGE)])
    )
    def post(self, request: Request):
        """创建产品"""
        try:
            serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                product = serializer.save()
                return result.success(ProductSerializer(product).data)
            else:
                return result.error(f"创建产品失败: {serializer.errors}")
        except Exception as e:
            return result.error(f"创建产品失败: {str(e)}")


class ProductPageView(APIView):
    authentication_classes = [TokenAuth]

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_summary=_("Get paginated product list"),
                         operation_id=_("Get paginated product list"),
                         tags=[_("Product")],
                         manual_parameters=[
                             openapi.Parameter(name='name', in_=openapi.IN_QUERY, type=openapi.TYPE_STRING,
                                             description='产品名称'),
                             openapi.Parameter(name='category', in_=openapi.IN_QUERY, type=openapi.TYPE_STRING,
                                             description='产品分类'),
                             openapi.Parameter(name='status', in_=openapi.IN_QUERY, type=openapi.TYPE_STRING,
                                             description='产品状态'),
                         ])
    @has_permissions(
        ViewPermission([RoleConstants.ADMIN, RoleConstants.USER],
                       [Permission(group=Group.APPLICATION, operate=Operate.USE)])
    )
    def get(self, request: Request, current_page: int, page_size: int):
        """获取分页产品列表"""
        try:
            query_params = query_params_to_single_dict(request.query_params)
            name = query_params.get('name', '')
            category = query_params.get('category', '')
            status = query_params.get('status', '')

            # 构建查询条件
            query = Q()
            if name:
                query &= Q(product_name__icontains=name)
            if category:
                query &= Q(product_type__icontains=category)

            products = Product.objects.filter(query).order_by('-created_at')
            
            # 计算分页
            total = products.count()
            start = (current_page - 1) * page_size
            end = start + page_size
            records = products[start:end]
            
            # 序列化数据
            serializer = ProductSerializer(records, many=True)
            
            # 返回分页结果
            page_data = Page(total, serializer.data, current_page, page_size)
            return result.success(page_data)
        except Exception as e:
            return result.error(f"获取产品列表失败: {str(e)}")


class ProductDetailView(APIView):
    authentication_classes = [TokenAuth]

    @action(methods=['GET'], detail=True)
    @swagger_auto_schema(operation_summary=_("Get product detail"),
                         operation_id=_("Get product detail"),
                         tags=[_("Product")])
    @has_permissions(
        ViewPermission([RoleConstants.ADMIN, RoleConstants.USER],
                       [Permission(group=Group.APPLICATION, operate=Operate.USE)])
    )
    def get(self, request: Request, product_id: str):
        """获取产品详情"""
        try:
            product = Product.objects.get(pk=product_id)
            serializer = ProductSerializer(product)
            return result.success(serializer.data)
        except Product.DoesNotExist:
            return result.error("产品不存在")
        except Exception as e:
            return result.error(f"获取产品详情失败: {str(e)}")

    @action(methods=['PUT'], detail=True)
    @swagger_auto_schema(operation_summary=_("Update product"),
                         operation_id=_("Update product"),
                         tags=[_("Product")],
                         request_body=ProductSerializer)
    @has_permissions(
        ViewPermission([RoleConstants.ADMIN],
                       [Permission(group=Group.APPLICATION, operate=Operate.MANAGE)])
    )
    def put(self, request: Request, product_id: str):
        """更新产品"""
        try:
            product = Product.objects.get(pk=product_id)
            serializer = ProductSerializer(product, data=request.data, partial=True)
            if serializer.is_valid():
                product = serializer.save()
                return result.success(ProductSerializer(product).data)
            else:
                return result.error(f"更新产品失败: {serializer.errors}")
        except Product.DoesNotExist:
            return result.error("产品不存在")
        except Exception as e:
            return result.error(f"更新产品失败: {str(e)}")

    @action(methods=['DELETE'], detail=True)
    @swagger_auto_schema(operation_summary=_("Delete product"),
                         operation_id=_("Delete product"),
                         tags=[_("Product")])
    @has_permissions(
        ViewPermission([RoleConstants.ADMIN],
                       [Permission(group=Group.APPLICATION, operate=Operate.MANAGE)])
    )
    def delete(self, request: Request, product_id: str):
        """删除产品"""
        try:
            product = Product.objects.get(pk=product_id)
            product.delete()
            return result.success(True)
        except Product.DoesNotExist:
            return result.error("产品不存在")
        except Exception as e:
            return result.error(f"删除产品失败: {str(e)}")


class ProductBatchView(APIView):
    authentication_classes = [TokenAuth]

    @action(methods=['POST'], detail=False)
    @swagger_auto_schema(operation_summary=_("Batch delete products"),
                         operation_id=_("Batch delete products"),
                         tags=[_("Product")],
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             properties={
                                 'ids': openapi.Schema(type=openapi.TYPE_ARRAY, 
                                                     items=openapi.Schema(type=openapi.TYPE_STRING),
                                                     description='产品ID列表')
                             }
                         ))
    @has_permissions(
        ViewPermission([RoleConstants.ADMIN],
                       [Permission(group=Group.APPLICATION, operate=Operate.MANAGE)])
    )
    def post(self, request: Request):
        """批量删除产品"""
        try:
            ids = request.data.get('ids', [])
            if not ids:
                return result.error("请选择要删除的产品")
            
            deleted_count = Product.objects.filter(id__in=ids).delete()[0]
            return result.success(f"成功删除 {deleted_count} 个产品")
        except Exception as e:
            return result.error(f"批量删除产品失败: {str(e)}")


class ProductCategoryView(APIView):
    authentication_classes = [TokenAuth]

    @action(methods=['GET'], detail=False)
    @swagger_auto_schema(operation_summary=_("Get product categories"),
                         operation_id=_("Get product categories"),
                         tags=[_("Product")])
    @has_permissions(
        ViewPermission([RoleConstants.ADMIN, RoleConstants.USER],
                       [Permission(group=Group.APPLICATION, operate=Operate.USE)])
    )
    def get(self, request: Request):
        """获取产品分类列表"""
        try:
            categories = Product.objects.values_list('product_type', flat=True).distinct()
            category_list = [{"label": cat, "value": cat} for cat in categories if cat]
            return result.success(category_list)
        except Exception as e:
            return result.error(f"获取产品分类失败: {str(e)}")


class ProductExportView(APIView):
    authentication_classes = [TokenAuth]

    @action(methods=['POST'], detail=False)
    @swagger_auto_schema(operation_summary=_("Export products"),
                         operation_id=_("Export products"),
                         tags=[_("Product")])
    @has_permissions(
        ViewPermission([RoleConstants.ADMIN],
                       [Permission(group=Group.APPLICATION, operate=Operate.MANAGE)])
    )
    def post(self, request: Request):
        """导出产品数据"""
        try:
            # 这里可以实现Excel导出逻辑
            # 暂时返回成功状态
            return result.success("导出功能待实现")
        except Exception as e:
            return result.error(f"导出产品数据失败: {str(e)}")


class ProductImportView(APIView):
    authentication_classes = [TokenAuth]

    @action(methods=['POST'], detail=False)
    @swagger_auto_schema(operation_summary=_("Import products"),
                         operation_id=_("Import products"),
                         tags=[_("Product")])
    @has_permissions(
        ViewPermission([RoleConstants.ADMIN],
                       [Permission(group=Group.APPLICATION, operate=Operate.MANAGE)])
    )
    def post(self, request: Request):
        """导入产品数据"""
        try:
            # 这里可以实现Excel导入逻辑
            # 暂时返回成功状态
            return result.success("导入功能待实现")
        except Exception as e:
            return result.error(f"导入产品数据失败: {str(e)}") 