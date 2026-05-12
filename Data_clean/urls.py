from django.urls import path
from . import views

app_name = 'Data_clean'

urlpatterns = [
    path('', views.index, name='index'),
]
