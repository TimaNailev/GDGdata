import pandas as pd
import streamlit as st
from logger import add_log, checkpoint_state


def show_numeric_cleaning(df: pd.DataFrame):
    st.subheader("Numeric Cleaning — Outlier Detection")

    if st.session_state.get("clean_df") is None:
        st.session_state["clean_df"] = df.copy()

    working_df = st.session_state["clean_df"]

    from utils import get_columns_by_type
    numeric_cols = get_columns_by_type(working_df, "numeric")

    if not numeric_cols:
        st.info("No numeric columns found in your dataset.")
        return

    selected_col = st.selectbox("Select numeric column", numeric_cols, key="num_clean_column")
    if not selected_col:
        st.info("Please select a column to continue.")
        return

    series = working_df[selected_col].dropna()
    if series.empty:
        st.warning("This column contains only missing values.")
        return

    # IQR CALCULATION
    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    full_series = working_df[selected_col]
    outlier_mask = (full_series < lower_bound) | (full_series > upper_bound)
    outlier_count = int(outlier_mask.sum())
    outlier_pct = round(outlier_count / len(full_series) * 100, 2)

    st.markdown("### IQR Analysis")
    row1 = st.columns(3)
    row1[0].metric("Q1 (25th percentile)", f"{q1:,.4f}")
    row1[1].metric("Q3 (75th percentile)", f"{q3:,.4f}")
    row1[2].metric("IQR", f"{iqr:,.4f}")

    row2 = st.columns(4)
    row2[0].metric("Lower Bound", f"{lower_bound:,.4f}")
    row2[1].metric("Upper Bound", f"{upper_bound:,.4f}")
    row2[2].metric("Outliers", f"{outlier_count}")
    row2[3].metric("Outlier %", f"{outlier_pct}%")
    st.divider()

    if outlier_count > 0:
        with st.expander(f"View {outlier_count} outlier row(s)", expanded=False):
            outlier_rows = working_df[outlier_mask]
            st.dataframe(outlier_rows.head(50), use_container_width=True)
    else:
        st.success("No outliers detected in this column.")
        return

    st.divider()

    # ACTION BUTTONS
    st.markdown("### Outlier Treatment")
    action_cols = st.columns(3)
    actions = ["Cap Values", "Remove Rows", "Do Nothing"]

    for i, action_name in enumerate(actions):
        is_selected = st.session_state.get("num_outlier_action") == action_name
        if action_cols[i].button(action_name, use_container_width=True, key=f"num_action_{i}", type="primary" if is_selected else "secondary"):
            st.session_state["num_outlier_action"] = action_name
            st.rerun()

    selected_action = st.session_state.get("num_outlier_action")
    if not selected_action:
        st.info("Select a treatment method above.")
        return

    st.divider()

    if selected_action == "Cap Values":
        st.markdown("### Cap (Winsorize) Outliers")
        st.caption(
            f"Values below **{lower_bound:,.4f}** will be set to {lower_bound:,.4f}. "
            f"Values above **{upper_bound:,.4f}** will be set to {upper_bound:,.4f}."
        )
        st.markdown("**Preview**")
        capped_preview = full_series.clip(lower=lower_bound, upper=upper_bound)
        prev_cols = st.columns(2)

        with prev_cols[0]:
            st.markdown("*Original (outliers only)*")
            orig_outliers = full_series[outlier_mask].head(10)
            st.dataframe(pd.DataFrame({"Original": orig_outliers.values}), use_container_width=True, hide_index=True)

        with prev_cols[1]:
            st.markdown("*After capping*")
            capped_outliers = capped_preview[outlier_mask].head(10)
            st.dataframe(pd.DataFrame({"Capped": capped_outliers.values}), use_container_width=True, hide_index=True)

        values_capped = int((full_series != capped_preview).sum())
        st.caption(f"{values_capped} value(s) will be capped.")

        if st.button("Apply Capping", key="apply_num_cap"):
            checkpoint_state()
            working_df[selected_col] = working_df[selected_col].clip(lower=lower_bound, upper=upper_bound)
            st.session_state["clean_df"] = working_df
            add_log("Cap Outliers", {"lower": round(lower_bound, 4), "upper": round(upper_bound, 4)}, [selected_col], rows_affected={"values_capped": values_capped})
            st.success(f"Capped {values_capped} outlier value(s) in '{selected_col}'.")
            st.rerun()

    elif selected_action == "Remove Rows":
        st.markdown("### Remove Outlier Rows")
        st.caption(
            f"Removes all rows where **{selected_col}** is "
            f"below {lower_bound:,.4f} or above {upper_bound:,.4f}."
        )
        rows_before = len(working_df)
        filtered = working_df[~outlier_mask]
        rows_after = len(filtered)
        rows_removed = rows_before - rows_after

        impact_cols = st.columns(3)
        impact_cols[0].metric("Rows Before", rows_before)
        impact_cols[1].metric("Rows Removed", rows_removed)
        impact_cols[2].metric("Rows After", rows_after)

        if st.button("Apply Row Removal", key="apply_num_remove"):
            checkpoint_state()
            st.session_state["clean_df"] = filtered
            add_log("Remove Outlier Rows", f"Removed {rows_removed} rows", [selected_col], rows_affected={"rows_deleted": rows_removed})
            st.success(f"Removed {rows_removed} outlier row(s).")
            st.rerun()

    elif selected_action == "Do Nothing":
        st.markdown("### No Treatment")
        st.caption("You've chosen to keep all outlier values as-is. This is a valid choice when outliers represent real data.")
        st.info(f"{outlier_count} outlier(s) will remain unchanged in '{selected_col}'.")


def show_normalization_scaling(df: pd.DataFrame):
    st.subheader("Normalization / Scaling")

    if st.session_state.get("clean_df") is None:
        st.session_state["clean_df"] = df.copy()

    working_df = st.session_state["clean_df"]

    from utils import get_columns_by_type
    numeric_cols = get_columns_by_type(working_df, "numeric")
    if not numeric_cols:
        st.info("No numeric columns found in your dataset.")
        return

    selected_cols = st.multiselect("Select numeric columns to scale", numeric_cols, key="scaling_columns")
    if not selected_cols:
        st.info("Select one or more numeric columns to continue.")
        return

    st.divider()

    # METHOD SELECTION
    st.markdown("### Scaling Method")
    method_cols = st.columns(2)
    methods = ["Min-Max Scaling", "Z-Score Standardization"]

    for i, method_name in enumerate(methods):
        is_selected = st.session_state.get("scaling_method") == method_name
        if method_cols[i].button(method_name, use_container_width=True, key=f"scale_method_{i}", type="primary" if is_selected else "secondary"):
            st.session_state["scaling_method"] = method_name
            st.rerun()

    selected_method = st.session_state.get("scaling_method")
    if not selected_method:
        st.info("Select a scaling method above.")
        return

    st.divider()

    # BEFORE STATS
    st.markdown("### Current Statistics")
    before_data = []
    for col_name in selected_cols:
        s = working_df[col_name].dropna()
        before_data.append({
            "Column": col_name,
            "Mean": round(float(s.mean()), 4) if len(s) > 0 else 0,
            "Std": round(float(s.std()), 4) if len(s) > 1 else 0,
            "Min": round(float(s.min()), 4) if len(s) > 0 else 0,
            "Max": round(float(s.max()), 4) if len(s) > 0 else 0,
        })
    before_df = pd.DataFrame(before_data)
    st.dataframe(before_df, use_container_width=True, hide_index=True)
    st.divider()

    # PREVIEW AFTER SCALING
    st.markdown("### Preview After Scaling")
    skipped_cols = []
    preview_data = []

    for col_name in selected_cols:
        s = working_df[col_name].dropna()
        if selected_method == "Min-Max Scaling":
            col_min = float(s.min()) if len(s) > 0 else 0
            col_max = float(s.max()) if len(s) > 0 else 0
            col_range = col_max - col_min
            if col_range == 0:
                skipped_cols.append(col_name)
                preview_data.append({"Column": col_name, "New Mean": "⚠️ skipped", "New Std": "—", "New Min": "—", "New Max": "—"})
            else:
                scaled = (s - col_min) / col_range
                preview_data.append({"Column": col_name, "New Mean": round(float(scaled.mean()), 4), "New Std": round(float(scaled.std()), 4), "New Min": round(float(scaled.min()), 4), "New Max": round(float(scaled.max()), 4)})
        else:
            col_std = float(s.std()) if len(s) > 1 else 0
            if col_std == 0:
                skipped_cols.append(col_name)
                preview_data.append({"Column": col_name, "New Mean": "⚠️ skipped", "New Std": "—", "New Min": "—", "New Max": "—"})
            else:
                scaled = (s - s.mean()) / col_std
                preview_data.append({"Column": col_name, "New Mean": round(float(scaled.mean()), 4), "New Std": round(float(scaled.std()), 4), "New Min": round(float(scaled.min()), 4), "New Max": round(float(scaled.max()), 4)})

    preview_df = pd.DataFrame(preview_data)
    st.dataframe(preview_df, use_container_width=True, hide_index=True)

    if skipped_cols:
        st.warning(f"⚠️ Column(s) **{', '.join(skipped_cols)}** have zero variance and will be skipped (division by zero).")

    # Side-by-side sample preview
    st.markdown("**Sample Values (first 8 rows)**")
    sample_cols = st.columns(2)
    with sample_cols[0]:
        st.markdown("*Before*")
        st.dataframe(working_df[selected_cols].head(8), use_container_width=True, hide_index=True)
    with sample_cols[1]:
        st.markdown("*After*")
        preview_scaled = working_df[selected_cols].head(8).copy()
        for col_name in selected_cols:
            if col_name in skipped_cols:
                continue
            s_full = working_df[col_name].dropna()
            if selected_method == "Min-Max Scaling":
                col_min = float(s_full.min())
                col_max = float(s_full.max())
                col_range = col_max - col_min
                preview_scaled[col_name] = (preview_scaled[col_name] - col_min) / col_range
            else:
                col_mean = float(s_full.mean())
                col_std = float(s_full.std())
                preview_scaled[col_name] = (preview_scaled[col_name] - col_mean) / col_std
        st.dataframe(preview_scaled, use_container_width=True, hide_index=True)

    st.divider()

    cols_to_scale = [c for c in selected_cols if c not in skipped_cols]
    if not cols_to_scale:
        st.warning("No columns can be scaled (all have zero variance).")
        return

    if st.button("Apply Scaling", key="apply_scaling"):
        checkpoint_state()
        for col_name in cols_to_scale:
            s_full = working_df[col_name].dropna()
            if selected_method == "Min-Max Scaling":
                col_min = float(s_full.min())
                col_max = float(s_full.max())
                col_range = col_max - col_min
                working_df[col_name] = (working_df[col_name] - col_min) / col_range
            else:
                col_mean = float(s_full.mean())
                col_std = float(s_full.std())
                working_df[col_name] = (working_df[col_name] - col_mean) / col_std
        st.session_state["clean_df"] = working_df
        add_log(f"Scale/Normalize ({selected_method})", {"method": selected_method}, list(cols_to_scale), rows_affected={"columns_scaled": len(cols_to_scale)})
        st.success(f"Applied **{selected_method}** to {len(cols_to_scale)} column(s): {', '.join(cols_to_scale)}")
        st.rerun()
