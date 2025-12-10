"""
问题URL配置
"""
from django.urls import path
from . import views
from . import generate_views

app_name = 'questions'

urlpatterns = [
    path('', views.question_list_create, name='list_create'),  # GET: 获取列表, POST: 创建问题
    path('generate/', generate_views.generate_questions, name='generate_questions'),  # POST: 批量生成问题
    path('batch-delete/', views.question_batch_delete, name='batch_delete'),  # DELETE: 批量删除问题
    path('<str:question_id>/', views.question_detail_update_delete, name='detail_update_delete'),  # GET/PUT/DELETE
]

