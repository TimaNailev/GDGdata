import pandas as pd
import streamlit as st
from logger import add_log, checkpoint_state


def show_missing_values_cleaning(df: pd.DataFrame):
    st.subheader("Missing Values Handling")

    if st.session_state["clean_df"] is None:
        st.session_state["clean_df"] = df.copy()

    working_df = st.session_state["clean_df"]

    # 1. Missing Summary
    missing_counts = working_df.isnull().sum()
    total_rows = len(working_df)

    summary_df = pd.DataFrame({
        "Column": working_df.columns,
        "Missing Count": missing_counts.values,
        "Missing %": ((missing_counts / total_rows) * 100).round(2)
    })

    st.markdown("### Missing Values Overview")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    st.divider()

    # 2. Actions
    st.markdown("### Cleaning Actions")
    st.markdown("### Cleaning Actions")

    action_cols = st.columns(3)
    actions = ["Drop rows", "Drop columns (threshold)", "Fill missing values"]

    for i, action_name in enumerate(actions):
        col = action_cols[i]
        is_selected = st.session_state.get("cleaning_action") == action_name
        if col.button(action_name, use_container_width=True, type="primary" if is_selected else "secondary"):
            st.session_state["cleaning_action"] = action_name
            st.rerun()

    selected_action = st.session_state.get("cleaning_action")

    if selected_action == "Drop rows":
        missing_cols = working_df.columns[working_df.isnull().any()].tolist()
        if not missing_cols:
            st.success("No columns with missing values found. No rows need to be dropped.")
            return
            
        cols = st.multiselect("Select columns (showing only columns with Nulls)", missing_cols)
        if st.button("Apply Drop Rows") and cols:
            checkpoint_state()
            before = len(working_df)
            working_df = working_df.dropna(subset=cols)
            st.session_state["clean_df"] = working_df
            rows_dropped = before - len(working_df)
            add_log("Drop rows with missing values", "Rows containing Nulls were permanently removed", list(cols), rows_affected={"rows_deleted": rows_dropped})
            st.success(f"Removed {rows_dropped} rows")
            st.rerun()

    elif selected_action == "Drop columns (threshold)":
        threshold = st.slider("Threshold (%)", 0, 100, 50)
        if st.button("Apply Drop Columns"):
            checkpoint_state()
            missing_pct = working_df.isnull().mean() * 100
            cols_to_drop = missing_pct[missing_pct > threshold].index
            working_df = working_df.drop(columns=cols_to_drop)
            st.session_state["clean_df"] = working_df
            add_log("Drop Columns by Threshold", f"Threshold > {threshold}%", list(cols_to_drop), rows_affected={"columns_deleted": len(cols_to_drop)})
            st.success(f"Dropped {len(cols_to_drop)} columns")
            st.rerun()

    elif selected_action == "Fill missing values":
        missing_cols = working_df.columns[working_df.isnull().any()].tolist()
        if not missing_cols:
            st.success("No missing values found! Your dataset is already complete.")
            return

        col = st.selectbox("Select column (showing only columns with Nulls)", missing_cols)
        series = working_df[col]

        if pd.api.types.is_numeric_dtype(series):
            method = st.selectbox("Method", ["Mean", "Median", "Mode", "Constant"])
            if method == "Constant":
                value = st.number_input("Value")
            if st.button("Apply Fill"):
                checkpoint_state()
                if method == "Mean":
                    working_df[col] = series.fillna(series.mean())
                elif method == "Median":
                    working_df[col] = series.fillna(series.median())
                elif method == "Mode":
                    working_df[col] = series.fillna(series.mode()[0])
                else:
                    working_df[col] = series.fillna(value)
                st.session_state["clean_df"] = working_df
                cells_filled = int(series.isna().sum())
                fill_val = value if method == "Constant" else None
                add_log(f"Fill Missing (Numeric: {method})", {"method": method.lower(), "fill_value": fill_val}, [col], rows_affected={"cells_filled": cells_filled})
                st.success("Filled successfully")
        else:
            method = st.selectbox("Method", ["Mode", "Forward Fill", "Backward Fill", "Constant"])
            if method == "Constant":
                value = st.text_input("Value")
            if st.button("Apply Fill"):
                checkpoint_state()
                if method == "Mode":
                    working_df[col] = series.fillna(series.mode()[0])
                elif method == "Forward Fill":
                    working_df[col] = series.fillna(method="ffill")
                elif method == "Backward Fill":
                    working_df[col] = series.fillna(method="bfill")
                else:
                    working_df[col] = series.fillna(value)
                st.session_state["clean_df"] = working_df
                cells_filled = int(series.isna().sum())
                fill_val = value if method == "Constant" else None
                add_log(f"Fill Missing (Text: {method})", {"method": method.lower(), "fill_value": fill_val}, [col], rows_affected={"cells_filled": cells_filled})
                st.success("Filled successfully")

    st.divider()

    # 3. BEFORE / AFTER
    if st.button("Show new and old overview"):
        original_rows = len(df)
        new_rows = len(st.session_state["clean_df"])
        c1, c2 = st.columns(2)
        c1.metric("Original Rows", original_rows)
        c2.metric("Cleaned Rows", new_rows)
        original_cols = set(df.columns)
        new_cols = set(st.session_state["clean_df"].columns)
        removed_cols = list(original_cols - new_cols)
        st.write("Removed columns:", removed_cols)
