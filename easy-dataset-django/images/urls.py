"""
图像URL配置
"""
from django.urls import path
from . import views
from . import extra_views

app_name = 'images'

urlpatterns = [
    # 将具体路径放在前面，避免被通用路径匹配
    path('upload/', extra_views.upload_image, name='upload_single'),
    path('zip-import/', extra_views.zip_import, name='zip_import'),
    path('pdf-convert/', extra_views.pdf_convert, name='pdf_convert'),
    path('next-unanswered/', extra_views.next_unanswered, name='next_unanswered'),
    path('annotations/', extra_views.annotations, name='annotations'),
    path('questions/', extra_views.generate_questions, name='image_questions'),
    path('datasets/', extra_views.generate_datasets, name='image_datasets_generate'),
    path('<str:image_id>/update/', extra_views.update_image, name='image_update'),
    # 通用路径放在后面
    path('<str:image_id>/', views.image_detail, name='detail'),  # GET
    path('', views.image_list_import_delete, name='list_import_delete'),  # GET/POST/DELETE
]

