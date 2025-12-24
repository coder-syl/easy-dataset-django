from django.urls import path
from . import views

app_name = "dataset_square"

urlpatterns = [
    path("sites/", views.sites_list, name="sites_list"),
    path("sites/<int:pk>/", views.site_detail, name="site_detail"),
]


