import pandas as pd
import streamlit as st
import numpy as np
import re

def get_columns_by_type(df: pd.DataFrame, kind: str) -> list:
    """
    Filter dataframe columns by their detected data type kind.
    Kinds: 'numeric', 'categorical', 'datetime'
    """
    if df is None:
        return []
        
    cols = []
    for col in df.columns:
        series = df[col]
        
        # Numeric Check
        if kind == "numeric":
            if pd.api.types.is_numeric_dtype(series):
                cols.append(col)
        
        # Categorical Check
        elif kind == "categorical":
            # Either object/category or low cardi-numeric that isn't primarily numeric
            if pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series):
                cols.append(col)
        
        # Datetime Check
        elif kind == "datetime":
            if pd.api.types.is_datetime64_any_dtype(series):
                cols.append(col)
            else:
                # Try a sample conversion to see if it's date-like
                try:
                    sample = series.dropna().head(10)
                    if not sample.empty and pd.to_datetime(sample, errors='coerce').notna().all():
                        cols.append(col)
                except:
                    pass
                    
    return cols

def get_all_column_types(df: pd.DataFrame) -> dict:
    """Returns a mapping of {col_name: simplified_type}"""
    types = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            types[col] = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            types[col] = "datetime"
        else:
            types[col] = "categorical"
    return types

def smart_parse_numeric(value):
    """
    Universal parser to convert complex strings into numeric values.
    Handles:
    - Feet/Inches (5'7", 6ft 2in) -> total inches
    - Fractions (1 1/2, 3/4) -> decimals
    - Percentages (50%) -> 0.5
    - Unit suffixes (159lbs, 72kg) -> numbers
    """
    if pd.isna(value) or value == "": 
        return np.nan
        
    s = str(value).strip().lower()
    
    # 1. Feet/Inches (5' 7", 5'7, 6ft 2in)
    match_ft_in = re.search(r"(\d+)'\s*(\d+)\"?", s) or re.search(r"(\d+)\s*ft\s*(\d+)\s*in", s)
    if match_ft_in:
        try:
            ft = float(match_ft_in.group(1))
            inch = float(match_ft_in.group(2))
            return ft * 12 + inch
        except: pass

    # 2. Fractions (e.g., 1 1/2)
    match_frac_mixed = re.search(r"(\d+)\s+(\d+)/(\d+)", s)
    if match_frac_mixed:
        try:
            whole = float(match_frac_mixed.group(1))
            num = float(match_frac_mixed.group(2))
            den = float(match_frac_mixed.group(3))
            return whole + (num / den)
        except: pass

    # 3. Simple Fraction (e.g., 3/4)
    match_frac_simple = re.match(r"^(\d+)/(\d+)$", s)
    if match_frac_simple:
        try:
            num = float(match_frac_simple.group(1))
            den = float(match_frac_simple.group(2))
            return num / den
        except: pass

    # 4. Percentages (e.g., 50.5%)
    if s.endswith("%"):
        try:
            return float(s.replace("%", "").strip()) / 100
        except: pass

    # 5. Scientific Notation / Standard Numbers / Financial Multipliers (K, M, B)
    # Detect multiplier suffixes before stripping letters
    multiplier = 1
    if s.endswith('k'): multiplier = 1e3
    elif s.endswith('m'): multiplier = 1e6
    elif s.endswith('b'): multiplier = 1e9
    
    # Remove currency and other non-numeric symbols except scientific 'e'
    # Keep digits, dots, signs, and 'e'
    s_clean = re.sub(r"[^0-9.e\-]", "", s)
    
    try:
        # If successfully cleaned, convert and multiply
        if s_clean:
            return float(s_clean) * multiplier
    except:
        pass
        
    return np.nan
