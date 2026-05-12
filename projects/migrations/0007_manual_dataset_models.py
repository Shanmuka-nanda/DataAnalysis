from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_remove_project_user_project_created_by_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('file', models.FileField(upload_to='datasets/')),
                ('version', models.IntegerField(default=1)),
                ('row_count', models.IntegerField(default=0)),
                ('column_count', models.IntegerField(default=0)),
                ('size', models.BigIntegerField(default=0)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('change_summary', models.TextField(blank=True, null=True)),
                ('parent_dataset', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='projects.dataset')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='datasets', to='projects.project')),
            ],
        ),
        migrations.CreateModel(
            name='ColumnSchema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column_name', models.CharField(max_length=200)),
                ('data_type', models.CharField(max_length=50)),
                ('is_numeric', models.BooleanField(default=False)),
                ('is_datetime', models.BooleanField(default=False)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='columns', to='projects.dataset')),
            ],
        ),
        migrations.CreateModel(
            name='DatasetProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stats_json', models.JSONField(default=dict)),
                ('dataset', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='projects.dataset')),
            ],
        ),
    ]
