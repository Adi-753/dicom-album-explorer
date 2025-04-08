import pandas as pd
import re
import numpy as np
from datetime import datetime

class QueryEngine:
    """
    Engine for querying DICOM metadata
    """
    
    @staticmethod
    def simple_query(df, field, value, operator='='):
        """
        Perform a simple query on a single field
        
        Parameters:
        - df: DataFrame with DICOM metadata
        - field: Field name to query
        - value: Value to match
        - operator: Comparison operator (=, !=, >, <, >=, <=, contains)
        
        Returns:
        - DataFrame with filtered results
        """
        if field not in df.columns:
            return pd.DataFrame()
        
        if operator == '=':
            return df[df[field].astype(str) == str(value)]
        elif operator == '!=':
            return df[df[field].astype(str) != str(value)]
        elif operator == '>':
            try:
                return df[pd.to_numeric(df[field], errors='coerce') > float(value)]
            except:
                return df[df[field].astype(str) > str(value)]
        elif operator == '<':
            try:
                return df[pd.to_numeric(df[field], errors='coerce') < float(value)]
            except:
                return df[df[field].astype(str) < str(value)]
        elif operator == '>=':
            try:
                return df[pd.to_numeric(df[field], errors='coerce') >= float(value)]
            except:
                return df[df[field].astype(str) >= str(value)]
        elif operator == '<=':
            try:
                return df[pd.to_numeric(df[field], errors='coerce') <= float(value)]
            except:
                return df[df[field].astype(str) <= str(value)]
        elif operator == 'contains':
            return df[df[field].astype(str).str.contains(str(value), case=False, na=False)]
        elif operator == 'starts_with':
            return df[df[field].astype(str).str.startswith(str(value), na=False)]
        elif operator == 'ends_with':
            return df[df[field].astype(str).str.endswith(str(value), na=False)]
        elif operator == 'regex':
            return df[df[field].astype(str).str.match(str(value), na=False)]
        else:
            return pd.DataFrame()
    
    @staticmethod
    def advanced_query(df, query_conditions, join_operator='AND'):
        """
        Perform an advanced query with multiple conditions
        
        Parameters:
        - df: DataFrame with DICOM metadata
        - query_conditions: List of dicts with field, value, and operator
        - join_operator: How to combine conditions (AND/OR)
        
        Returns:
        - DataFrame with filtered results
        """
        if not query_conditions:
            return df
        
        result_frames = []
        
        for condition in query_conditions:
            field = condition.get('field')
            value = condition.get('value')
            operator = condition.get('operator', '=')
            
            if field and value is not None:
                query_result = QueryEngine.simple_query(df, field, value, operator)
                result_frames.append(query_result)
        
        if not result_frames:
            return pd.DataFrame()
        
        # Combine results based on join_operator
        if join_operator.upper() == 'AND':
            # For AND, we need the intersection of all result sets
            # Start with all rows from the first result
            final_result = result_frames[0]
            
            # Find the intersection with each subsequent result
            for frame in result_frames[1:]:
                # Find common indices
                common_indices = final_result.index.intersection(frame.index)
                final_result = final_result.loc[common_indices]
            
            return final_result
            
        elif join_operator.upper() == 'OR':
            # For OR, we combine all unique rows
            return pd.concat(result_frames).drop_duplicates()
        
        return pd.DataFrame()
    
    @staticmethod
    def date_range_query(df, field, start_date, end_date):
        """
        Query for dates within a specific range
        
        Parameters:
        - df: DataFrame with DICOM metadata
        - field: Date field name
        - start_date: Start date (YYYYMMDD format)
        - end_date: End date (YYYYMMDD format)
        
        Returns:
        - DataFrame with filtered results
        """
        if field not in df.columns:
            return pd.DataFrame()
        
        try:
            df_dates = pd.to_datetime(df[field], format='%Y%m%d', errors='coerce')
            start = pd.to_datetime(start_date, format='%Y%m%d')
            end = pd.to_datetime(end_date, format='%Y%m%d')
            
            return df[(df_dates >= start) & (df_dates <= end)]
        except:
            return pd.DataFrame()
    
    @staticmethod
    def modality_query(df, modalities):
        """
        Query for specific modalities
        
        Parameters:
        - df: DataFrame with DICOM metadata
        - modalities: List of modalities to include
        
        Returns:
        - DataFrame with filtered results
        """
        if 'Modality' not in df.columns or not modalities:
            return pd.DataFrame()
        
        return df[df['Modality'].astype(str).isin([str(m) for m in modalities])]
    
    @staticmethod
    def generate_query_summary(query_conditions, join_operator='AND'):
        """Generate a human-readable summary of the query"""
        if not query_conditions:
            return "No query conditions specified"
        
        condition_texts = []
        
        for condition in query_conditions:
            field = condition.get('field', '')
            value = condition.get('value', '')
            operator = condition.get('operator', '=')
            
            operator_text = {
                '=': 'equals',
                '!=': 'does not equal',
                '>': 'is greater than',
                '<': 'is less than',
                '>=': 'is greater than or equal to',
                '<=': 'is less than or equal to',
                'contains': 'contains',
                'starts_with': 'starts with',
                'ends_with': 'ends with',
                'regex': 'matches regex'
            }.get(operator, operator)
            
            condition_texts.append(f"{field} {operator_text} '{value}'")
        
        join_text = f" {join_operator} "
        return join_text.join(condition_texts)
    