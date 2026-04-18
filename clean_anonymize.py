import pandas as pd
import streamlit as st
import re
from logger import add_log, checkpoint_state

def infer_prefix(col_name: str) -> str:
    """Infer a default pseudonym prefix from the column name."""
    low = col_name.lower()
    if any(k in low for k in ["emp", "staff", "worker"]): return "Employee"
    if any(k in low for k in ["cust", "client", "buyer"]): return "Customer"
    if any(k in low for k in ["user", "login", "account"]): return "User"
    if any(k in low for k in ["name", "person", "subject"]): return "Person"
    if any(k in low for k in ["email", "contact", "address"]): return "Contact"
    return "Entity"

def mask_text(val, keep_first=0, keep_last=0, mask_char="*") -> str:
    """Apply masking logic to a single value."""
    if pd.isna(val) or val is None:
        return val
    s = str(val)
    if len(s) <= (keep_first + keep_last):
        return s # Not enough length to mask middle
    
    middle_len = len(s) - keep_first - keep_last
    mask = mask_char * middle_len
    
    first_part = s[:keep_first]
    last_part = s[-keep_last:] if keep_last > 0 else ""
    
    return first_part + mask + last_part

def show_anonymization_cleaning(df: pd.DataFrame):
    """Renders the Anonymization toolkit."""
    st.subheader("Data Anonymization")
    st.caption("Protect sensitive information using Masking or Pseudonymization.")

    if st.session_state.get("clean_df") is None:
        st.session_state["clean_df"] = df.copy()
    working_df = st.session_state["clean_df"]

    all_cols = working_df.columns.tolist()
    selected_col = st.selectbox("Select column to anonymize", all_cols, key="anon_col")

    if not selected_col:
        st.info("Please select a column.")
        return

    method = st.radio("Select Anonymization Method", ["Masking", "Pseudonymization"], horizontal=True, key="anon_method")

    series = working_df[selected_col]
    preview = series.copy()
    params = {}

    if method == "Masking":
        st.write("---")
        st.markdown("#### Masking Settings")
        c1, c2, c3 = st.columns(3)
        keep_first = c1.number_input("Keep First N", 0, 50, 0, key="anon_mask_first")
        keep_last = c2.number_input("Keep Last N", 0, 50, 0, key="anon_mask_last")
        mask_char = c3.text_input("Mask Character", "*", max_chars=1, key="anon_mask_char")
        
        preview = series.apply(lambda x: mask_text(x, keep_first, keep_last, mask_char))
        params = {"method": "masking", "keep_first": keep_first, "keep_last": keep_last, "char": mask_char}

    else: # Pseudonymization
        st.write("---")
        st.markdown("#### Pseudonymization Settings")
        suggested_prefix = infer_prefix(selected_col)
        prefix = st.text_input("Pseudonym Prefix", value=suggested_prefix, key="anon_pseudo_prefix")
        
        st.caption("Stable mapping: The same original value will always get the same pseudonym.")
        
        # Build stable mapping
        unique_vals = series.dropna().unique()
        mapping = {val: f"{prefix}_{str(i+1).zfill(3)}" for i, val in enumerate(unique_vals)}
        
        preview = series.map(mapping)
        params = {"method": "pseudonymization", "prefix": prefix}

    # PREVIEW
    st.write("---")
    st.markdown("**Preview**")
    p_cols = st.columns(2)
    with p_cols[0]:
        st.markdown("*Original*")
        st.dataframe(pd.DataFrame({"Original": series.head(10).values}), use_container_width=True, hide_index=True)
    with p_cols[1]:
        st.markdown(f"*Anonymized ({method})*")
        st.dataframe(pd.DataFrame({f"{method}": preview.head(10).values}), use_container_width=True, hide_index=True)

    # ACTION
    new_col_name = f"{selected_col}_anon"
    overwrite = st.checkbox(f"Overwrite original column '{selected_col}'", value=False, key="anon_overwrite")
    target_col = selected_col if overwrite else new_col_name

    if st.button(f"Apply {method}", type="primary", use_container_width=True):
        checkpoint_state()
        
        # Apply logic to whole working_df
        if method == "Masking":
            working_df[target_col] = working_df[selected_col].apply(lambda x: mask_text(x, keep_first, keep_last, mask_char))
        else:
            # Re-build mapping for full data to be safe
            unique_vals = working_df[selected_col].dropna().unique()
            mapping = {val: f"{prefix}_{str(i+1).zfill(3)}" for i, val in enumerate(unique_vals)}
            working_df[target_col] = working_df[selected_col].map(mapping)
            params["mapping_size"] = len(mapping)

        st.session_state["clean_df"] = working_df
        add_log(f"Anonymization ({method})", params, [target_col], rows_affected={"rows_modified": len(working_df)})
        st.success(f"Anonymization applied. Cleaned data in: **{target_col}**")
        st.rerun()
