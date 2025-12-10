"""
批量生成GA对URL配置
"""
from django.urls import path
from . import views

app_name = 'files_batch'

urlpatterns = [
    path('', views.batch_generate_ga, name='batch_generate_ga'),  # POST: 批量生成GA对
]

