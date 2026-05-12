from django.db import models
from django.conf import settings

class Project(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('analyzed', 'Analyzed'),
    )

    workspace = models.ForeignKey('accounts.Workspace', on_delete=models.CASCADE, related_name='projects', null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_projects', null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    dataset = models.FileField(upload_to='datasets/', null=True, blank=True)
    file_type = models.CharField(max_length=10, default='csv')
    dataset_size = models.IntegerField(default=0)
    total_rows = models.IntegerField(default=0)
    total_columns = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Dataset(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='datasets')
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='datasets/')
    version = models.IntegerField(default=1)
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    size = models.BigIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parent_dataset = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    change_summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.project.name} - {self.name} (v{self.version})"

class ColumnSchema(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='columns')
    column_name = models.CharField(max_length=200)
    data_type = models.CharField(max_length=50) # int, float, string, date, bool
    is_numeric = models.BooleanField(default=False)
    is_datetime = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.column_name} ({self.dataset.name})"

class DatasetProfile(models.Model):
    dataset = models.OneToOneField(Dataset, on_delete=models.CASCADE, related_name='profile')
    stats_json = models.JSONField(default=dict)
    
    def __str__(self):
        return f"Profile for {self.dataset.name}"