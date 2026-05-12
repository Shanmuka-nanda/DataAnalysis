import os
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from projects.models import Project
from .models import Visualization, Dashboard, Measure
from services.aggregation_service import get_visualization_data
from django.db.models import Count
from accounts.models import Activity


def _get_user_primary_goal(user):
    profile = getattr(user, 'profile', None)
    company = getattr(profile, 'company', None) if profile else None
    return getattr(company, 'primary_goal', 'General') if company else 'General'


def _goal_labels(primary_goal):
    labels = {
        'Recruitment': {
            'dashboard_name': 'Recruitment Intelligence Overview',
            'kpi_title': 'Hiring KPI',
            'bar_prefix': 'Hiring Funnel by',
            'pie_title': 'Candidate Segment Distribution',
        },
        'Company Growth': {
            'dashboard_name': 'Company Growth Overview',
            'kpi_title': 'Growth KPI',
            'bar_prefix': 'Growth Analysis by',
            'pie_title': 'Growth Segment Distribution',
        },
        'Sales': {
            'dashboard_name': 'Sales Intelligence Overview',
            'kpi_title': 'Sales KPI',
            'bar_prefix': 'Sales Analysis by',
            'pie_title': 'Sales Segment Distribution',
        },
        'General': {
            'dashboard_name': 'Business Intelligence Overview',
            'kpi_title': 'Key Performance Metric',
            'bar_prefix': 'Analysis by',
            'pie_title': 'Segment Distribution',
        }
    }
    return labels.get(primary_goal, labels['General'])


def _keyword_buckets(primary_goal):
    buckets = {
        'Recruitment': {
            'numeric': ['salary', 'ctc', 'offer', 'score', 'experience', 'days', 'time', 'cost', 'age'],
            'categorical': ['status', 'source', 'department', 'role', 'position', 'location', 'recruiter', 'stage'],
            'segment': ['source', 'department', 'role', 'location', 'status'],
        },
        'Company Growth': {
            'numeric': ['revenue', 'mrr', 'arr', 'growth', 'user', 'customer', 'retention', 'churn', 'signup', 'conversion', 'profit'],
            'categorical': ['month', 'quarter', 'year', 'region', 'segment', 'plan', 'channel', 'cohort'],
            'segment': ['segment', 'plan', 'region', 'channel', 'cohort'],
        },
        'Sales': {
            'numeric': ['revenue', 'sales', 'amount', 'value', 'price', 'profit', 'target', 'quota', 'discount'],
            'categorical': ['region', 'product', 'category', 'segment', 'channel', 'salesperson', 'stage', 'account', 'customer'],
            'segment': ['product', 'category', 'region', 'segment', 'channel'],
        },
        'General': {
            'numeric': ['amount', 'value', 'total', 'count', 'score', 'price', 'cost'],
            'categorical': ['category', 'type', 'status', 'segment', 'group', 'region'],
            'segment': ['segment', 'category', 'type', 'region'],
        }
    }
    return buckets.get(primary_goal, buckets['General'])


def _column_score(column_name, keywords):
    normalized = (column_name or '').lower().replace('_', ' ').replace('-', ' ')
    score = 0
    for keyword in keywords:
        if keyword in normalized:
            score += len(keyword)
    return score


def _pick_best_column(columns, keywords, exclude_names=None):
    exclude_names = exclude_names or set()
    candidates = [col for col in columns if col.column_name not in exclude_names]
    if not candidates:
        return None

    best_col = None
    best_score = -1
    for col in candidates:
        current_score = _column_score(col.column_name, keywords)
        if current_score > best_score:
            best_col = col
            best_score = current_score

    if best_col and best_score > 0:
        return best_col
    return candidates[0]


def _recommend_columns(primary_goal, num_cols, cat_cols):
    buckets = _keyword_buckets(primary_goal)
    numeric_cols = list(num_cols)
    categorical_cols = list(cat_cols)

    numeric_pick = _pick_best_column(numeric_cols, buckets['numeric']) if numeric_cols else None
    group_pick = _pick_best_column(categorical_cols, buckets['categorical']) if categorical_cols else None

    exclude_names = {group_pick.column_name} if group_pick else set()
    segment_pick = _pick_best_column(categorical_cols, buckets['segment'], exclude_names=exclude_names) if categorical_cols else None

    if numeric_pick:
        return {
            'measure_column': numeric_pick.column_name,
            'aggregation_type': 'SUM',
            'measure_name': f"Total {numeric_pick.column_name}",
            'group_by': group_pick.column_name if group_pick else '',
            'segment_by': segment_pick.column_name if segment_pick else '',
        }

    count_column = group_pick.column_name if group_pick else (categorical_cols[0].column_name if categorical_cols else '')
    return {
        'measure_column': count_column,
        'aggregation_type': 'COUNT',
        'measure_name': 'Record Count',
        'group_by': group_pick.column_name if group_pick else '',
        'segment_by': segment_pick.column_name if segment_pick else '',
    }


def _build_default_visuals(dashboard, dataset, primary_goal):
    from projects.models import ColumnSchema
    from analytics.models import DashboardFilter

    num_cols = ColumnSchema.objects.filter(dataset=dataset, is_numeric=True)
    cat_cols = ColumnSchema.objects.filter(dataset=dataset, is_numeric=False)

    if not num_cols.exists() and not cat_cols.exists():
        return False

    rec = _recommend_columns(primary_goal, num_cols, cat_cols)
    goal_labels = _goal_labels(primary_goal)

    measure_col = rec['measure_column']
    if not measure_col:
        return False

    target_measure, _ = Measure.objects.get_or_create(
        dataset=dataset,
        name=rec['measure_name'],
        column_name=measure_col,
        aggregation_type=rec['aggregation_type']
    )

    Visualization.objects.create(
        dashboard=dashboard,
        title=goal_labels['kpi_title'],
        type='card',
        measure=target_measure,
        grid_x=0,
        grid_y=0,
        grid_w=3,
        grid_h=2
    )

    group_by = rec['group_by']
    if group_by:
        Visualization.objects.create(
            dashboard=dashboard,
            title=f"{goal_labels['bar_prefix']} {group_by}",
            type='bar',
            measure=target_measure,
            group_by=group_by,
            grid_x=3,
            grid_y=0,
            grid_w=9,
            grid_h=4
        )

        DashboardFilter.objects.get_or_create(
            dashboard=dashboard,
            column_name=group_by,
            filter_type='dropdown',
            defaults={'label': f"Filter by {group_by}"}
        )

    segment_by = rec['segment_by']
    if segment_by and segment_by != group_by:
        Visualization.objects.create(
            dashboard=dashboard,
            title=goal_labels['pie_title'],
            type='pie',
            measure=target_measure,
            group_by=segment_by,
            grid_x=0,
            grid_y=2,
            grid_w=3,
            grid_h=3
        )

    return True

@login_required
def index(request):
    # --- Self-healing DB check ---
    from django.db import connection
    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analytics_dashboard';")
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
            # Create analytics tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_measure (
                    id integer PRIMARY KEY AUTOINCREMENT,
                    name varchar(100) NOT NULL,
                    column_name varchar(100) NOT NULL,
                    aggregation_type varchar(20) NOT NULL,
                    dataset_id bigint NOT NULL REFERENCES projects_dataset(id)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_dashboard (
                    id integer PRIMARY KEY AUTOINCREMENT,
                    name varchar(200) NOT NULL,
                    layout_json json NOT NULL,
                    created_at datetime NOT NULL,
                    created_by_id bigint NOT NULL REFERENCES accounts_user(id),
                    project_id bigint NOT NULL REFERENCES projects_project(id)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_visualization (
                    id integer PRIMARY KEY AUTOINCREMENT,
                    type varchar(50) NOT NULL,
                    title varchar(200) NOT NULL,
                    x_axis varchar(100) NOT NULL,
                    y_axis varchar(100) NOT NULL,
                    group_by varchar(100) NOT NULL,
                    filters_json json NOT NULL,
                    grid_x integer NOT NULL,
                    grid_y integer NOT NULL,
                    grid_w integer NOT NULL,
                    grid_h integer NOT NULL,
                    dashboard_id bigint NOT NULL REFERENCES analytics_dashboard(id),
                    measure_id bigint NULL REFERENCES analytics_measure(id)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_dashboardfilter (
                    id integer PRIMARY KEY AUTOINCREMENT,
                    column_name varchar(100) NOT NULL,
                    filter_type varchar(50) NOT NULL,
                    label varchar(100) NOT NULL,
                    dashboard_id bigint NOT NULL REFERENCES analytics_dashboard(id)
                );
            """)
            # Mark migrations
            cursor.execute("INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES ('projects', '0007_manual_dataset_models', datetime('now'));")
            cursor.execute("INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES ('analytics', '0001_initial', datetime('now'));")
    # --- End self-healing ---
    
    user = request.user
    primary_goal = _get_user_primary_goal(user)
    goal_labels = _goal_labels(primary_goal)
    project_id = request.GET.get('project_id')

    # 2. Total Projects
    workspace = user.get_active_workspace()
    projects = Project.objects.filter(workspace=workspace)
    active_projects = projects.count()
    
    proj_limit = 20  # Arbitrary max free-tier limit
    proj_percentage = min(100, int((active_projects / proj_limit) * 100)) if proj_limit else 0
    proj_dashoffset = 251.2 - (251.2 * (proj_percentage / 100.0))
    
    # 3. Data Volume Processed
    total_bytes = 0
    for p in projects:
        try:
            if p.dataset and hasattr(p.dataset, 'size'):
                total_bytes += p.dataset.size
        except Exception:
            pass # In case file doesn't exist on disk
            
    total_mb = round(total_bytes / (1024 * 1024), 2)
    
    quota_limit = 200 # 200 MB user limit
    quota_percentage = min(100, int((total_mb / quota_limit) * 100)) if quota_limit else 0
    quota_dashoffset = 251.2 - (251.2 * (quota_percentage / 100.0))

    # 4. Total Rows Analyzed
    total_rows = sum(p.total_rows for p in projects if p.total_rows)
    row_limit = 1000000 # Arbitrary 1M row limit
    row_percentage = min(100, int((total_rows / row_limit) * 100)) if row_limit else 0
    row_dashoffset = 251.2 - (251.2 * (row_percentage / 100.0))

    # Calculate Breakdown by File Type
    file_types = {'csv': 0, 'excel': 0, 'json': 0}
    for p in projects:
        ext = 'csv'
        if p.dataset and getattr(p.dataset, 'name', None):
            name = str(p.dataset.name).lower()
            if name.endswith('.xlsx') or name.endswith('.xls'):
                ext = 'excel'
            elif name.endswith('.json'):
                ext = 'json'
        file_types[ext] += 1
    
    total_files = sum(file_types.values()) or 1 # Prevent div by zero
    csv_pct = int((file_types['csv'] / total_files) * 100)
    excel_pct = int((file_types['excel'] / total_files) * 100)
    json_pct = 100 - csv_pct - excel_pct # remaining

    dashboards = Dashboard.objects.filter(project__workspace=workspace).order_by('-created_at')

    top_actions = list(
        Activity.objects.filter(user=user)
        .values('title')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    # Helper: ensure we have ColumnSchema metadata for a dataset
    def ensure_metadata(dataset):
        from projects.models import ColumnSchema
        from services.dataset_service import analyze_dataset

        if not dataset:
            return

        # If no schema rows exist yet, analyze the dataset file now
        if not ColumnSchema.objects.filter(dataset=dataset).exists():
            try:
                analyze_dataset(dataset.id)
            except Exception as e:
                print(f"Failed to analyze dataset {dataset.id}: {e}")
                # If analysis fails, we silently continue; visuals just won't be created.
                return

    # Helper: always get a Dataset for a project, even for older projects that
    # only have the legacy project.dataset file populated.
    def get_or_create_primary_dataset(project):
        from projects.models import Dataset

        dataset = Dataset.objects.filter(project=project).order_by('-uploaded_at').first()
        if not dataset and getattr(project, 'dataset', None):
            file_field = project.dataset
            if file_field:
                name = os.path.basename(getattr(file_field, 'name', '') or "dataset.csv")
                size = getattr(file_field, 'size', 0) or 0
                dataset = Dataset.objects.create(
                    project=project,
                    name=name,
                    file=file_field,
                    size=size,
                )
        return dataset

    # Auto-generate a default dashboard for the workspace if none exist but datasets are available
    if not dashboards.exists():
        from projects.models import Dataset
        # Grab the most recently created Dataset in this workspace
        dataset = Dataset.objects.filter(project__workspace=workspace).order_by('-uploaded_at').first()
        if dataset:
            ensure_metadata(dataset)
            project = dataset.project
            if dataset:
                db = Dashboard.objects.create(
                    project=project,
                    name=goal_labels['dashboard_name'],
                    created_by=user
                )
                _build_default_visuals(db, dataset, primary_goal)

            # Refresh dashboards query
            dashboards = Dashboard.objects.filter(project__workspace=workspace)

    # Determine which dashboard should be auto-selected
    selected_dashboard_id = None

    if project_id:
        try:
            # Ensure the project belongs to the active workspace
            target_project = Project.objects.get(id=project_id, workspace=workspace)
        except Project.DoesNotExist:
            target_project = None

        if target_project:
            project_dashboards = dashboards.filter(project=target_project)

            # If this project has no dashboard yet, auto-generate one using its latest dataset
            if not project_dashboards.exists():
                from projects.models import Dataset
                dataset = get_or_create_primary_dataset(target_project)
                if dataset:
                    ensure_metadata(dataset)
                    db = Dashboard.objects.create(
                        project=target_project,
                        name=f"{target_project.name} - {goal_labels['dashboard_name']}",
                        created_by=user
                    )
                    _build_default_visuals(db, dataset, primary_goal)

                    # Refresh dashboard query for this project
                    dashboards = Dashboard.objects.filter(project__workspace=workspace)
                    project_dashboards = dashboards.filter(project=target_project)

            if project_dashboards.exists():
                selected_dashboard_id = project_dashboards.first().id
    else:
        # Fallback: pick the first dashboard in the workspace
        first = dashboards.first()
        if first:
            selected_dashboard_id = first.id

    context = {
        'active_projects': active_projects,
        'proj_percentage': proj_percentage,
        'proj_dashoffset': round(proj_dashoffset, 2),
        
        'total_mb': total_mb,
        'quota_percentage': quota_percentage,
        'quota_dashoffset': round(quota_dashoffset, 2),
        
        'total_rows': total_rows,
        'row_percentage': row_percentage,
        'row_dashoffset': round(row_dashoffset, 2),
        'dashboards': dashboards,
        'selected_dashboard_id': selected_dashboard_id,
        'csv_pct': csv_pct,
        'excel_pct': excel_pct,
        'json_pct': json_pct,
        'primary_goal': primary_goal,
        'top_actions': top_actions,
    }

    return render(request, 'analytics/index.html', context)

@login_required
def get_visual_data(request, visual_id):
    """
    API endpoint to fetch data for a specific visualization.
    """
    # Security: Ensure visual belongs to a dashboard in a workspace the user has access to
    visual = get_object_or_404(Visualization, id=visual_id)
    
    # Check workspace membership
    if not visual.dashboard.project.workspace.members.filter(user=request.user).exists():
        return JsonResponse({'error': 'Unauthorized access to this visualization.'}, status=403)
        
    global_filters = request.GET.dict() # Get all query params as potential filters
    data = get_visualization_data(visual_id, global_filters=global_filters)
    return JsonResponse(data)

@login_required
def dashboard_detail_api(request, dashboard_id):
    """
    Returns the full configuration and layout of a dashboard.
    """
    dashboard = get_object_or_404(Dashboard, id=dashboard_id)

    if not dashboard.project.workspace.members.filter(user=request.user).exists():
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # If this dashboard has no visuals yet (older projects created before auto-setup),
    # try to auto-generate a default set of visuals now so the user sees charts.
    if not dashboard.visualizations.exists():
        from projects.models import Dataset, ColumnSchema
        from services.dataset_service import analyze_dataset
        primary_goal = _get_user_primary_goal(request.user)

        # Use the most recent dataset for this project
        dataset = Dataset.objects.filter(project=dashboard.project).order_by('-uploaded_at').first()
        if dataset:
            # Ensure we have column metadata
            if not ColumnSchema.objects.filter(dataset=dataset).exists():
                try:
                    analyze_dataset(dataset.id)
                except Exception as e:
                    print(f"Failed to analyze dataset {dataset.id} again: {e}")
                    dataset = None

        if dataset:
            _build_default_visuals(dashboard, dataset, primary_goal)

    return JsonResponse({
        'id': dashboard.id,
        'name': dashboard.name,
        'layout': dashboard.layout_json,
        'visuals': list(dashboard.visualizations.values('id', 'type', 'title', 'grid_x', 'grid_y', 'grid_w', 'grid_h')),
        'filters': list(dashboard.filters.values('id', 'column_name', 'filter_type', 'label'))
    })
