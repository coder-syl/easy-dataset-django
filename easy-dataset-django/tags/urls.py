"""
标签URL配置
"""
from django.urls import path
from . import views

app_name = 'tags'

urlpatterns = [
    path('', views.tag_tree, name='tree'),  # GET/POST/PUT/DELETE
]
