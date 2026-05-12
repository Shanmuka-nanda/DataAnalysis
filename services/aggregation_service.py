import pandas as pd
import numpy as np
# Removed top-level imports of analytics.models to prevent circular dependency

def get_visualization_data(visualization_id, global_filters=None):
    """
    Calculates the data for a visualization based on its configuration, measures, and filters.
    """
    from analytics.models import Visualization
    vis = Visualization.objects.select_related('dashboard', 'measure').get(id=visualization_id)
    
    # Identify the dataset to use
    dataset = None
    if vis.measure:
        dataset = vis.measure.dataset
    else:
        # Fallback to the latest dataset of the project
        dataset = vis.dashboard.project.datasets.order_by('-uploaded_at').first()
    
    if not dataset or not dataset.file:
        return {'success': False, 'error': 'No dataset associated with this visualization.'}
        
    try:
        # Load data (should be cached in a real production app)
        file_path = dataset.file.path
        if file_path.endswith('.csv'):
            try:
                df = pd.read_csv(file_path)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin1')
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return {'success': False, 'error': 'Unsupported file format.'}
        
        # 1. Apply Filtering
        active_filters = vis.filters_json.copy()
        if global_filters:
            active_filters.update(global_filters)
            
        for col, val in active_filters.items():
            if col in df.columns and val:
                # To support multiple values, e.g., if a frontend multi-select passes comma-separated values
                if isinstance(val, str) and ',' in val:
                    val_list = [v.strip() for v in val.split(',')]
                    df = df[df[col].astype(str).isin(val_list)]
                else:
                    df = df[df[col].astype(str) == str(val)]
                    
        # 1.5 Handle Nulls gracefully before group by
        if vis.group_by and vis.group_by in df.columns:
            df[vis.group_by] = df[vis.group_by].fillna('Unknown')

        # 2. Aggregation Logic
        
        # CASE A: KPI Card (Single Value)
        if vis.type == 'card':
            if not vis.measure:
                 return {'success': False, 'error': 'Card visualization requires a measure.'}
            
            value = calculate_measure(df, vis.measure)
            return {
                'type': 'card',
                'title': vis.title or vis.measure.name,
                'value': value
            }

        # CASE B: Grouped Visualizations (Bar, Pie, Line, Area)
        if vis.group_by:
            if not vis.measure:
                # If no measure, default to COUNT per group
                from analytics.models import Measure
                grouped = df.groupby(vis.group_by).size().reset_index(name='count')
                val_col = 'count'
            else:
                m = vis.measure
                agg_type = m.aggregation_type.upper()
                
                # Map Django choices to pandas agg functions
                agg_map = {
                    'SUM': 'sum',
                    'AVG': 'mean',
                    'COUNT': 'count',
                    'MIN': 'min',
                    'MAX': 'max'
                }
                agg_func = agg_map.get(agg_type, 'sum')
                
                grouped = df.groupby(vis.group_by)[m.column_name].agg(agg_func).reset_index()
                val_col = m.column_name

            # Sort for better presentation
            grouped = grouped.sort_values(by=val_col, ascending=False).head(20) # Limit to top 20 for charts
            
            return {
                'type': vis.type,
                'title': vis.title or (vis.measure.name if vis.measure else f"Count by {vis.group_by}"),
                'labels': grouped[vis.group_by].astype(str).tolist(),
                'data': grouped[val_col].replace({np.nan: None}).tolist()
            }
            
        return {'success': False, 'error': 'Visualization configuration is incomplete.'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def calculate_measure(df, measure):
    """
    Helper to calculate a single measure value on a (filtered) dataframe.
    """
    col = measure.column_name
    if col not in df.columns:
        return 0
        
    agg = measure.aggregation_type.upper()
    
    if agg == 'SUM':
        return float(df[col].sum())
    elif agg == 'AVG':
        return float(df[col].mean())
    elif agg == 'COUNT':
        return int(df[col].count())
    elif agg == 'MIN':
        return float(df[col].min())
    elif agg == 'MAX':
        return float(df[col].max())
    return 0
