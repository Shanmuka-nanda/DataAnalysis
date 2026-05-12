from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('projects', '0007_manual_dataset_models'),
        migrations.swappable_dependency('accounts.User'),
    ]
    operations = [
        migrations.CreateModel(
            name='Measure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('column_name', models.CharField(max_length=100)),
                ('aggregation_type', models.CharField(choices=[('SUM', 'Sum'), ('AVG', 'Average'), ('COUNT', 'Count'), ('MIN', 'Minimum'), ('MAX', 'Maximum')], default='SUM', max_length=20)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='measures', to='projects.dataset')),
            ],
        ),
        migrations.CreateModel(
            name='Dashboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('layout_json', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.user')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analytics_dashboards', to='projects.project')),
            ],
        ),
        migrations.CreateModel(
            name='Visualization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('bar', 'Bar Chart'), ('line', 'Line Chart'), ('pie', 'Pie Chart'), ('table', 'Table'), ('card', 'KPI Card'), ('area', 'Area Chart')], default='bar', max_length=50)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('x_axis', models.CharField(blank=True, max_length=100)),
                ('y_axis', models.CharField(blank=True, max_length=100)),
                ('group_by', models.CharField(blank=True, max_length=100)),
                ('filters_json', models.JSONField(blank=True, default=dict)),
                ('grid_x', models.IntegerField(default=0)),
                ('grid_y', models.IntegerField(default=0)),
                ('grid_w', models.IntegerField(default=4)),
                ('grid_h', models.IntegerField(default=4)),
                ('dashboard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='visualizations', to='analytics.dashboard')),
                ('measure', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='analytics.measure')),
            ],
        ),
        migrations.CreateModel(
            name='DashboardFilter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column_name', models.CharField(max_length=100)),
                ('filter_type', models.CharField(choices=[('dropdown', 'Dropdown'), ('range', 'Range'), ('date', 'Date Selector')], default='dropdown', max_length=50)),
                ('label', models.CharField(blank=True, max_length=100)),
                ('dashboard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='filters', to='analytics.dashboard')),
            ],
        ),
    ]
