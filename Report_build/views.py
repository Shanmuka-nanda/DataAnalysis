from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from projects.models import Project, Dataset, ColumnSchema
import pandas as pd
import numpy as np
import json

@login_required
def index(request):
    # Fetch user's projects so they can select one to build a report for
    projects = []
    selected_project_id = request.GET.get('project_id')

    if request.user.is_authenticated:
        workspace = request.user.get_active_workspace()
        projects = Project.objects.filter(workspace=workspace)

    context = {
        'projects': projects,
        'selected_project_id': selected_project_id,
    }
    return render(request, 'Report_build/index.html', context)

@login_required
def get_report_data(request, project_id):
    workspace = request.user.get_active_workspace()
    project = get_object_or_404(Project, id=project_id, workspace=workspace)
    
    if not project.dataset:
        return JsonResponse({'error': 'No dataset found for this project.'}, status=400)
    
    try:
        if project.dataset.name.endswith('.csv'):
            try:
                df = pd.read_csv(project.dataset.path)
            except UnicodeDecodeError:
                df = pd.read_csv(project.dataset.path, encoding='latin1')
        elif project.dataset.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(project.dataset.path)
        else:
            return JsonResponse({'error': 'Unsupported file format.'}, status=400)
            
        # USE METADATA instead of re-detecting
        numeric_cols = list(ColumnSchema.objects.filter(dataset__project=project, is_numeric=True).values_list('column_name', flat=True))
        categorical_cols = list(ColumnSchema.objects.filter(dataset__project=project, is_numeric=False).values_list('column_name', flat=True))
        
        # If metadata missing (legacy), fallback
        if not numeric_cols:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
        
        # We might want to limit rows to 5000 to prevent browser crash
        if len(df) > 5000:
            df = df.sample(n=5000, random_state=42)
            
        # Handle Pandas to JSON conversion robustly (this handles NaNs, Dates perfectly)
        data = json.loads(df.to_json(orient='records', date_format='iso'))
        
        return JsonResponse({
            'success': True,
            'data': data,
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols,
            'total_rows': project.total_rows,
            'project_name': project.name
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

