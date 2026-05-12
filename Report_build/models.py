from django.db import models
from django.conf import settings
from projects.models import Project

class Dashboard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='report_dashboards')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_dashboards')
    name = models.CharField(max_length=200, default="My Dashboard")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"

class Widget(models.Model):
    CHART_TYPES = (
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('line', 'Line Chart'),
        ('scatter', 'Scatter Plot'),
        ('kpi', 'KPI Card'),
    )

    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    title = models.CharField(max_length=200, blank=True)
    chart_type = models.CharField(max_length=50, choices=CHART_TYPES, default='bar')
    
    # Data Mapping
    x_axis = models.CharField(max_length=100, blank=True, null=True)
    y_axis = models.CharField(max_length=100, blank=True, null=True)
    aggregation = models.CharField(max_length=50, default='count', blank=True) # count, sum, avg

    # GridStack.js Position Data
    grid_x = models.IntegerField(default=0)
    grid_y = models.IntegerField(default=0)
    grid_width = models.IntegerField(default=4)
    grid_height = models.IntegerField(default=4)

    def __str__(self):
        return f"{self.chart_type} Widget on {self.dashboard.name}"
