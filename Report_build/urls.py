from django.urls import path
from . import views

app_name = 'Report_build'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/data/<int:project_id>/', views.get_report_data, name='get_report_data'),
]
