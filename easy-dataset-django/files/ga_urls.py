"""
GA对生成（单文件）URL
"""
from django.urls import path
from . import ga_views

app_name = 'files_ga'

urlpatterns = [
    path('<str:file_id>/ga-pairs/', ga_views.generate_ga_for_file, name='ga_pairs'),
]

