import pandas as pd
import numpy as np
from projects.models import Dataset, ColumnSchema, DatasetProfile

def analyze_dataset(dataset_id):
    """
    Analyzes a dataset file to detect schema, data types, and generate statistical profiles.
    """
    dataset = Dataset.objects.get(id=dataset_id)
    file_path = dataset.file.path
    
    # Load data
    if file_path.endswith('.csv'):
        try:
            df = pd.read_csv(file_path)
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='latin1')
    elif file_path.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format")
    
    # Update dataset basic info
    dataset.row_count = len(df)
    dataset.column_count = len(df.columns)
    dataset.size = dataset.file.size
    dataset.save()
    
    # Detect Schema
    for col in df.columns:
        dtype = str(df[col].dtype)
        is_numeric = pd.api.types.is_numeric_dtype(df[col])
        
        # Improved datetime detection
        is_datetime = pd.api.types.is_datetime64_any_dtype(df[col])
        if not is_datetime and dtype == 'object':
            try:
                # Try to convert a sample to datetime to see if it's a date string
                sample = df[col].dropna().iloc[:5]
                if not sample.empty:
                    pd.to_datetime(sample)
                    is_datetime = True
            except (ValueError, TypeError):
                pass

        # Simplified type name for our metadata
        if is_numeric:
            type_name = 'float' if 'float' in dtype else 'int'
        elif is_datetime:
            type_name = 'date'
        elif dtype == 'bool':
            type_name = 'bool'
        else:
            type_name = 'string'
            
        ColumnSchema.objects.update_or_create(
            dataset=dataset,
            column_name=col,
            defaults={
                'data_type': type_name,
                'is_numeric': is_numeric,
                'is_datetime': is_datetime
            }
        )
    
    # Generate Profile (basic stats)
    stats = {}
    for col in df.columns:
        col_stats = {
            'null_count': int(df[col].isnull().sum()),
            'unique_count': int(df[col].nunique()),
            'null_percentage': round((df[col].isnull().sum() / len(df)) * 100, 2) if len(df) > 0 else 0
        }
        
        if pd.api.types.is_numeric_dtype(df[col]):
            def safe_num(val):
                return 0 if pd.isna(val) or np.isinf(val) else float(val)

            col_stats.update({
                'mean': safe_num(df[col].mean()) if not df[col].empty else 0,
                'max': safe_num(df[col].max()) if not df[col].empty else 0,
                'min': safe_num(df[col].min()) if not df[col].empty else 0,
                'median': safe_num(df[col].median()) if not df[col].empty else 0,
                'std': safe_num(df[col].std()) if not df[col].empty else 0,
            })
            
        stats[col] = col_stats
        
    DatasetProfile.objects.update_or_create(
        dataset=dataset,
        defaults={'stats_json': stats}
    )
    
    return dataset
