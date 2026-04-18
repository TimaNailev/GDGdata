import streamlit as st
import datetime
import copy

def checkpoint_state():
    """Call this BEFORE a destructive action (cleaning step or log deletion)"""
    if "app_history_undo" not in st.session_state:
        st.session_state["app_history_undo"] = []
    
    st.session_state["app_history_redo"] = [] # Clear redo on new action
    
    current_df = st.session_state.get("clean_df")
    current_logs = st.session_state.get("transformation_logs", [])
    
    snapshot_df = current_df.copy(deep=True) if current_df is not None else None
    snapshot_logs = copy.deepcopy(current_logs)
    
    st.session_state["app_history_undo"].append((snapshot_df, snapshot_logs))

def perform_undo():
    if not st.session_state.get("app_history_undo"):
        return False
        
    if "app_history_redo" not in st.session_state:
        st.session_state["app_history_redo"] = []
        
    current_df = st.session_state.get("clean_df")
    current_logs = st.session_state.get("transformation_logs", [])
    st.session_state["app_history_redo"].append((
        current_df.copy(deep=True) if current_df is not None else None,
        copy.deepcopy(current_logs)
    ))
    
    prev_df, prev_logs = st.session_state["app_history_undo"].pop()
    st.session_state["clean_df"] = prev_df
    st.session_state["transformation_logs"] = prev_logs
    return True

def perform_redo():
    if not st.session_state.get("app_history_redo"):
        return False
        
    if "app_history_undo" not in st.session_state:
        st.session_state["app_history_undo"] = []
        
    current_df = st.session_state.get("clean_df")
    current_logs = st.session_state.get("transformation_logs", [])
    st.session_state["app_history_undo"].append((
        current_df.copy(deep=True) if current_df is not None else None,
        copy.deepcopy(current_logs)
    ))
    
    next_df, next_logs = st.session_state["app_history_redo"].pop()
    st.session_state["clean_df"] = next_df
    st.session_state["transformation_logs"] = next_logs
    return True

def add_log(operation_name, parameters, columns, rows_affected=None):
    if "transformation_logs" not in st.session_state:
        st.session_state["transformation_logs"] = []
    
    current_df = st.session_state.get("clean_df", None)
    snapshot = current_df.copy(deep=True) if current_df is not None else None

    log_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "operation": operation_name,
        "parameters": parameters,
        "columns": columns,
        "rows_affected": rows_affected,
        "df_snapshot": snapshot
    }
    st.session_state["transformation_logs"].append(log_entry)
