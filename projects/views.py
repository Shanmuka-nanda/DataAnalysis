import os
import pandas as pd
from django.views.generic import ListView, CreateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from .models import Project
from .forms import ProjectCreateForm
from accounts.models import Activity
from django.db.models import Sum
from django.utils import timezone
import json
import datetime
from django.contrib import messages

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        # --- Self-healing DB check ---
        from django.db import connection
        with connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects_dataset';")
            if not cursor.fetchone():
                # Create projects tables
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS projects_dataset (
                        id integer PRIMARY KEY AUTOINCREMENT,
                        name varchar(200) NOT NULL,
                        file varchar(100) NOT NULL,
                        version integer NOT NULL,
                        row_count integer NOT NULL,
                        column_count integer NOT NULL,
                        size bigint NOT NULL,
                        uploaded_at datetime NOT NULL,
                        change_summary text NULL,
                        parent_dataset_id bigint NULL REFERENCES projects_dataset(id),
                        project_id bigint NOT NULL REFERENCES projects_project(id)
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS projects_columnschema (
                        id integer PRIMARY KEY AUTOINCREMENT,
                        column_name varchar(200) NOT NULL,
                        data_type varchar(50) NOT NULL,
                        is_numeric bool NOT NULL,
                        is_datetime bool NOT NULL,
                        dataset_id bigint NOT NULL REFERENCES projects_dataset(id)
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS projects_datasetprofile (
                        id integer PRIMARY KEY AUTOINCREMENT,
                        stats_json json NOT NULL,
                        dataset_id bigint NOT NULL UNIQUE REFERENCES projects_dataset(id)
                    );
                """)
                # Mark migrations
                cursor.execute("INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES ('projects', '0007_manual_dataset_models', datetime('now'));")
        # --- End self-healing ---

        workspace = self.request.user.get_active_workspace()
        return Project.objects.filter(workspace=workspace).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_size_bytes = self.get_queryset().aggregate(Sum('dataset_size'))['dataset_size__sum'] or 0
        used_storage = round(total_size_bytes / (1024 * 1024), 2)
        if total_size_bytes > 0 and used_storage == 0.0:
            used_storage = 0.01
            
        recent_activities = Activity.objects.filter(user=self.request.user).order_by('-created_at')[:5]
        
        # Calculate storage usage over time (last 6 months)
        monthly_storage = []
        months_labels = []
        today = timezone.now().date()
        
        for i in range(5, -1, -1):
            # Get the month and year for i months ago
            month_date = today.replace(day=1) - datetime.timedelta(days=i * 30)
            month_date = month_date.replace(day=1)  # Ensure it's the 1st of that month

            # Sum dataset size for projects created up to the end of that month
            workspace = self.request.user.get_active_workspace()
            next_month = (month_date.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
            next_month_dt = timezone.make_aware(
                datetime.datetime.combine(next_month, datetime.time.min),
                timezone.get_current_timezone()
            )
            storage_up_to_month = Project.objects.filter(
                workspace=workspace,
                created_at__lt=next_month_dt
            ).aggregate(Sum('dataset_size'))['dataset_size__sum'] or 0
            
            storage_mb = round(storage_up_to_month / (1024 * 1024), 2)
            if storage_up_to_month > 0 and storage_mb == 0.0:
                storage_mb = 0.01
                
            monthly_storage.append(storage_mb)
            months_labels.append(month_date.strftime('%b'))

        context['used_storage'] = used_storage
        context['recent_activities'] = recent_activities
        context['storage_chart_data'] = json.dumps(monthly_storage)
        context['storage_chart_labels'] = json.dumps(months_labels)
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectCreateForm
    template_name = 'projects/project_create.html'

    def form_valid(self, form):
        project = form.save(commit=False)
        project.workspace = self.request.user.get_active_workspace()
        project.created_by = self.request.user
        dataset_file = form.cleaned_data.get('dataset')

        if not dataset_file:
            form.add_error('dataset', 'Please upload a CSV or XLSX file before submitting.')
            return self.form_invalid(form)
        
        # Save project first to get an ID
        project.save()
        
        if dataset_file:
            from .models import Dataset
            from services.dataset_service import analyze_dataset
            
            # Create the metadata-ready Dataset record
            ds = Dataset.objects.create(
                project=project,
                name=dataset_file.name,
                file=dataset_file,
                size=dataset_file.size
            )
            
            # Trigger automatic analysis (Schema + Profile)
            try:
                analyze_dataset(ds.id)
                project.status = 'analyzed'
                messages.success(self.request, f"Dataset '{ds.name}' uploaded and analyzed successfully.")
            except Exception as e:
                # In a real app we'd log this or show a warning
                project.status = 'pending'
                messages.warning(self.request, f"Project created, but auto-analysis failed: {e}")
            
            # Update legacy fields for backward compatibility
            project.dataset_size = ds.size
            project.total_rows = ds.row_count
            project.total_columns = ds.column_count
            project.save()
            
            # Log activity
            Activity.objects.create(
                user=self.request.user,
                title=f"Uploaded Dataset: {ds.name}",
                description=f"Detected {ds.column_count} columns and {ds.row_count} rows in {project.name}.",
                date=timezone.now().date()
            )
            
            self.object = project
            return redirect(self.get_success_url())

        return self.form_invalid(form)

    def get_success_url(self):
        """
        After creating a project, optionally redirect back to a 'next' URL,
        automatically tagging the new project id as a query parameter.
        This lets flows like Analytics → New Dataset → Analytics work seamlessly.
        """
        next_url = self.request.POST.get('next')
        if next_url:
            try:
                from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

                parsed = urlparse(next_url)
                query = parse_qs(parsed.query)
                # Always expose the created project id so the target page can focus on it
                query['project_id'] = [str(self.object.pk)]
                new_query = urlencode(query, doseq=True)
                return urlunparse(parsed._replace(query=new_query))
            except Exception:
                # If anything goes wrong, just fall back to the raw next_url
                return next_url

        dashboard_url = reverse('analytics:index')
        return f"{dashboard_url}?project_id={self.object.pk}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = getattr(self.request.user, 'profile', None)
        company = getattr(profile, 'company', None) if profile else None
        primary_goal = getattr(company, 'primary_goal', 'General') if company else 'General'

        goal_hints = {
            'Recruitment': 'Use hiring pipeline files: candidates, interviews, status, source, recruiter.',
            'Company Growth': 'Use growth KPIs: revenue, customers, churn, retention, MRR, month-over-month.',
            'Sales': 'Use sales data: deal stage, account, region, revenue, conversion, pipeline.',
            'General': 'Upload any clean CSV/XLSX dataset and the app will auto-detect the best structure.'
        }

        context['company_name'] = getattr(company, 'name', '') if company else ''
        context['primary_goal'] = primary_goal
        context['goal_hint'] = goal_hints.get(primary_goal, goal_hints['General'])
        return context

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        workspace = self.request.user.get_active_workspace()
        # Enforce security so only owners/members can view
        return Project.objects.filter(workspace=workspace)

class DeleteProjectView(LoginRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('projects:project_list')

    def get_queryset(self):
        workspace = self.request.user.get_active_workspace()
        return Project.objects.filter(workspace=workspace)

