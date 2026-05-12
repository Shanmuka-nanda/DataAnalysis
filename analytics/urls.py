from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/visual/<int:visual_id>/', views.get_visual_data, name='visual_data_api'),
    path('api/dashboard/<int:dashboard_id>/', views.dashboard_detail_api, name='dashboard_detail_api'),
]
