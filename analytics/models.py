from django.db import models
from django.conf import settings

class Measure(models.Model):
    AGGREGATION_CHOICES = (
        ('SUM', 'Sum'),
        ('AVG', 'Average'),
        ('COUNT', 'Count'),
        ('MIN', 'Minimum'),
        ('MAX', 'Maximum'),
    )
    dataset = models.ForeignKey('projects.Dataset', on_delete=models.CASCADE, related_name='measures')
    name = models.CharField(max_length=100)
    column_name = models.CharField(max_length=100)
    aggregation_type = models.CharField(max_length=20, choices=AGGREGATION_CHOICES, default='SUM')

    def __str__(self):
        return f"{self.name} ({self.aggregation_type})"

class Dashboard(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='analytics_dashboards')
    name = models.CharField(max_length=200)
    layout_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Visualization(models.Model):
    VIS_TYPES = (
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('table', 'Table'),
        ('card', 'KPI Card'),
        ('area', 'Area Chart'),
    )
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='visualizations')
    type = models.CharField(max_length=50, choices=VIS_TYPES, default='bar')
    title = models.CharField(max_length=200, blank=True)
    
    # Data Mapping
    measure = models.ForeignKey(Measure, on_delete=models.SET_NULL, null=True, blank=True)
    x_axis = models.CharField(max_length=100, blank=True)
    y_axis = models.CharField(max_length=100, blank=True) # Used if No measure
    group_by = models.CharField(max_length=100, blank=True)
    
    filters_json = models.JSONField(default=dict, blank=True)
    
    # Layout Config (Used by GridStack)
    grid_x = models.IntegerField(default=0)
    grid_y = models.IntegerField(default=0)
    grid_w = models.IntegerField(default=4)
    grid_h = models.IntegerField(default=4)

    def __str__(self):
        return f"{self.title or self.type} on {self.dashboard.name}"

class DashboardFilter(models.Model):
    FILTER_TYPES = (
        ('dropdown', 'Dropdown'),
        ('range', 'Range'),
        ('date', 'Date Selector'),
    )
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='filters')
    column_name = models.CharField(max_length=100)
    filter_type = models.CharField(max_length=50, choices=FILTER_TYPES, default='dropdown')
    label = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Filter: {self.column_name}"
