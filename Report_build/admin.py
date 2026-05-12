from django.contrib import admin
from .models import Dashboard, Widget

class WidgetInline(admin.TabularInline):
    model = Widget
    extra = 0

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'project', 'created_at')
    inlines = [WidgetInline]

@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'dashboard', 'chart_type', 'x_axis', 'y_axis', 'aggregation')
    list_filter = ('chart_type', 'dashboard')
