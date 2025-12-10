"""
数据蒸馏URL配置
"""
from django.urls import path
from . import views

app_name = 'distill'

urlpatterns = [
    path('questions/', views.distill_questions, name='questions'),  # POST: 蒸馏问题
    path('questions/by-tag/', views.distill_questions_by_tag, name='questions_by_tag'),  # POST: 按标签蒸馏问题
    path('tags/', views.distill_tags, name='tags'),  # GET/POST: 获取可蒸馏标签/蒸馏标签
    path('tags/all/', views.distill_all_tags, name='tags_all'),  # POST: 蒸馏所有标签
    path('tags/<str:tag_id>/', views.distill_tag_by_id, name='tags_by_id'),  # POST: 蒸馏指定标签
]

