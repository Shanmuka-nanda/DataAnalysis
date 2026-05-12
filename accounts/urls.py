from django.urls import path
from .views import login_view, register_view, logout_view, profile_view, update_theme, onboarding_view, notifications_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('notifications/', notifications_view, name='notifications'),
    path('update_theme/', update_theme, name='update_theme'),
    path('onboarding/', onboarding_view, name='onboarding'),
]