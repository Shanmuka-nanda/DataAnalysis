from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import Activity, Workspace, WorkspaceMember
from projects.models import Project
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone

@login_required
def dashboard_view(request):
    workspace = request.user.get_active_workspace()

    period = request.GET.get('period', 'week')
    period_map = {
        'day': 1,
        'week': 7,
        'month': 30,
    }
    if period not in period_map:
        period = 'week'

    period_days = period_map[period]
    period_label_map = {
        'day': 'Today',
        'week': 'This Week',
        'month': 'This Month',
    }
    period_label = period_label_map[period]

    today = timezone.localdate()
    current_start = today - timedelta(days=period_days - 1)
    previous_start = current_start - timedelta(days=period_days)
    previous_end = current_start - timedelta(days=1)

    current_activity_qs = Activity.objects.filter(
        user=request.user,
        date__gte=current_start,
        date__lte=today,
    )
    previous_activity_qs = Activity.objects.filter(
        user=request.user,
        date__gte=previous_start,
        date__lte=previous_end,
    )

    current_project_qs = Project.objects.filter(
        workspace=workspace,
        created_at__date__gte=current_start,
        created_at__date__lte=today,
    )
    previous_project_qs = Project.objects.filter(
        workspace=workspace,
        created_at__date__gte=previous_start,
        created_at__date__lte=previous_end,
    )

    def compute_change(current_value, previous_value):
        if previous_value == 0:
            if current_value == 0:
                return 0
            return 100
        return round(((current_value - previous_value) / previous_value) * 100)

    total_activities = current_activity_qs.count()
    prev_total_activities = previous_activity_qs.count()
    activities_change = compute_change(total_activities, prev_total_activities)

    recent_activities = Activity.objects.filter(user=request.user).order_by('-date')[:5]

    total_projects = current_project_qs.count()
    prev_total_projects = previous_project_qs.count()
    projects_change = compute_change(total_projects, prev_total_projects)

    recent_projects = Project.objects.filter(workspace=workspace).order_by("-created_at")[:4]

    active_users = WorkspaceMember.objects.filter(workspace=workspace).count()

    avg_processing_time = round(total_activities / period_days, 2) if period_days else 0
    prev_avg_processing_time = round(prev_total_activities / period_days, 2) if period_days else 0
    processing_change = compute_change(avg_processing_time, prev_avg_processing_time)

    # Activity trend based on selected period
    dates = [today - timedelta(days=x) for x in range(period_days)]
    dates.reverse()

    daily_activity_counts = {d: 0 for d in dates}
    for row in current_activity_qs.values('date'):
        d = row['date']
        if d in daily_activity_counts:
            daily_activity_counts[d] += 1

    df_trend = pd.DataFrame({
        'Date': pd.to_datetime(list(daily_activity_counts.keys())),
        'Activities': list(daily_activity_counts.values())
    })
    
    fig_trend = px.line(df_trend, x='Date', y='Activities', title=f'Activity Trend ({period_label})', 
                        markers=True, color_discrete_sequence=['#4F46E5'])
    fig_trend.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title=None,
        yaxis_title=None,
        height=300
    )
    chart_trend = fig_trend.to_html(full_html=False, include_plotlyjs=False)

    # Project distribution based on real status values
    status_labels = {
        'analyzed': 'Completed',
        'processing': 'In Progress',
        'pending': 'Pending',
    }
    status_counts = {'Completed': 0, 'In Progress': 0, 'Pending': 0, 'Archived': 0}
    for status in Project.objects.filter(workspace=workspace).values_list('status', flat=True):
        label = status_labels.get(status, 'Archived')
        status_counts[label] += 1

    df_dist = pd.DataFrame({
        'Status': list(status_counts.keys()),
        'Count': list(status_counts.values())
    })
    fig_dist = px.bar(df_dist, x='Status', y='Count', title='Projects by Status',
                      color='Status', color_discrete_sequence=['#10B981', '#3B82F6', '#F59E0B', '#6B7280'])
    fig_dist.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title=None,
        yaxis_title=None,
        height=300,
        showlegend=False
    )
    chart_dist = fig_dist.to_html(full_html=False, include_plotlyjs=False)

    context = {
        'period': period,
        'period_label': period_label,
        'total_activities': total_activities,
        'activities_change': activities_change,
        'recent_activities': recent_activities,
        'total_projects': total_projects,
        'projects_change': projects_change,
        'active_users': active_users,
        'avg_processing_time': avg_processing_time,
        'processing_change': processing_change,
        'recent_projects': recent_projects,
        'current_workspace': workspace,
        'chart_trend': chart_trend,
        'chart_dist': chart_dist
    }
    return render(request, 'dashboard.html', context)
