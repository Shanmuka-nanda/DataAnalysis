from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('projects', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='Dashboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='My Dashboard', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='report_dashboards', to='projects.project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_dashboards', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Widget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=200)),
                ('chart_type', models.CharField(choices=[('bar', 'Bar Chart'), ('pie', 'Pie Chart'), ('line', 'Line Chart'), ('scatter', 'Scatter Plot'), ('kpi', 'KPI Card')], default='bar', max_length=50)),
                ('x_axis', models.CharField(blank=True, max_length=100, null=True)),
                ('y_axis', models.CharField(blank=True, max_length=100, null=True)),
                ('aggregation', models.CharField(blank=True, default='count', max_length=50)),
                ('grid_x', models.IntegerField(default=0)),
                ('grid_y', models.IntegerField(default=0)),
                ('grid_width', models.IntegerField(default=4)),
                ('grid_height', models.IntegerField(default=4)),
                ('dashboard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='widgets', to='Report_build.dashboard')),
            ],
        ),
    ]
