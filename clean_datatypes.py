import pandas as pd
import streamlit as st
from logger import add_log, checkpoint_state


def show_data_types_cleaning(df: pd.DataFrame):
    st.subheader("Data Type Conversion")

    if st.session_state.get("clean_df") is None:
        st.session_state["clean_df"] = df.copy()

    working_df = st.session_state["clean_df"]

    # COLUMN OVERVIEW TABLE
    st.markdown("### Column Overview")
    total_rows = len(working_df)
    overview_data = []
    for col_name in working_df.columns:
        series = working_df[col_name]
        sample_val = series.dropna().iloc[0] if series.dropna().shape[0] > 0 else "N/A"
        overview_data.append({
            "Column": col_name,
            "Current Type": str(series.dtype),
            "Sample Value": str(sample_val)[:60],
            "Missing": int(series.isna().sum()),
            "Missing %": round(series.isna().mean() * 100, 2)
        })
    overview_df = pd.DataFrame(overview_data)
    st.dataframe(overview_df, use_container_width=True, hide_index=True)
    st.divider()

    # SUB-MODULE SELECTOR
    st.markdown("### Conversion Tools")
    tool_cols = st.columns(3)
    tools = ["Convert to Numeric", "Convert to Datetime", "Convert to Categorical"]

    for i, tool_name in enumerate(tools):
        is_selected = st.session_state.get("dtype_tool") == tool_name
        if tool_cols[i].button(tool_name, use_container_width=True, key=f"dtype_tool_{i}", type="primary" if is_selected else "secondary"):
            st.session_state["dtype_tool"] = tool_name
            st.rerun()

    selected_tool = st.session_state.get("dtype_tool")

    # CONVERT TO NUMERIC
    if selected_tool == "Convert to Numeric":
        st.markdown("### Convert to Numeric")
        st.caption("Converts text into numbers. Use 'Smart Mode' for complex formats like 5'7\", 159lbs, or 1 1/2.")

        non_numeric_cols = [
            c for c in working_df.columns
            if not pd.api.types.is_numeric_dtype(working_df[c])
        ]
        if not non_numeric_cols:
            st.success("All columns are already numeric!")
            return

        selected_cols = st.multiselect("Select columns to convert", non_numeric_cols, key="dtype_numeric_cols")
        use_smart = st.checkbox("🚀 Use Smart Universal Parser", value=True, help="Automatically handles Feet/Inches, Fractions, Units (lbs/kg), and Percentages.", key="dtype_numeric_smart")

        if selected_cols:
            from utils import smart_parse_numeric
            st.markdown("**Preview (first 8 rows)**")
            preview_df = pd.DataFrame()
            
            for col_name in selected_cols:
                original = working_df[col_name].head(8)
                if use_smart:
                    converted = working_df[col_name].apply(smart_parse_numeric)
                else:
                    cleaned = (
                        working_df[col_name].astype(str)
                        .str.replace(r'[\$€£¥,\s]', '', regex=True).str.strip()
                    )
                    converted = pd.to_numeric(cleaned, errors="coerce")
                
                preview_df[f"{col_name} (original)"] = original.values
                preview_df[f"{col_name} (converted)"] = converted.head(8).values
            st.dataframe(preview_df, use_container_width=True, hide_index=True)

            # Failure check
            for col_name in selected_cols:
                if use_smart:
                    converted_full = working_df[col_name].apply(smart_parse_numeric)
                else:
                    cleaned_full = (
                        working_df[col_name].astype(str)
                        .str.replace(r'[\$€£¥,\s]', '', regex=True).str.strip()
                    )
                    converted_full = pd.to_numeric(cleaned_full, errors="coerce")
                
                failed = int(converted_full.isna().sum() - working_df[col_name].isna().sum())
                if failed > 0:
                    msg = f"⚠️ **{col_name}**: {failed} value(s) could not be parsed and will become NaN."
                    if not use_smart:
                        # Extra hint if suffixes are detected
                        if working_df[col_name].astype(str).str.contains(r'[kmbKMB]', regex=True, na=False).any():
                            msg += " **Try enabling 'Smart Universal Parser' to handle K/M multipliers.**"
                    st.warning(msg)

            if st.button("Apply Numeric Conversion", key="apply_numeric"):
                checkpoint_state()
                for col_name in selected_cols:
                    if use_smart:
                        working_df[col_name] = working_df[col_name].apply(smart_parse_numeric)
                    else:
                        cleaned = (
                            working_df[col_name].astype(str)
                            .str.replace(r'[\$€£¥,\s]', '', regex=True).str.strip()
                        )
                        working_df[col_name] = pd.to_numeric(cleaned, errors="coerce")
                
                st.session_state["clean_df"] = working_df
                mode_str = "smart_parser" if use_smart else "standard_strip"
                add_log("Convert to Numeric", {"mode": mode_str}, list(selected_cols), rows_affected={"columns_converted": len(selected_cols)})
                st.success(f"Converted {len(selected_cols)} column(s) to numeric using {mode_str}.")
                st.rerun()

    # CONVERT TO DATETIME
    elif selected_tool == "Convert to Datetime":
        st.markdown("### Convert to Datetime")
        st.caption("Parse date/time strings into proper datetime objects.")

        non_dt_cols = [
            c for c in working_df.columns
            if not pd.api.types.is_datetime64_any_dtype(working_df[c])
        ]
        if not non_dt_cols:
            st.success("All applicable columns are already datetime!")
            return

        selected_col = st.selectbox("Select column to convert", non_dt_cols, key="dtype_datetime_col")

        if selected_col:
            st.markdown("**Sample values**")
            sample_vals = working_df[selected_col].dropna().head(5).tolist()
            st.code("\n".join(str(v) for v in sample_vals))

            format_options = [
                "Auto (let pandas detect)", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
                "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "Custom"
            ]
            chosen_format = st.selectbox("Date format", format_options, key="dtype_datetime_format")

            custom_format = None
            if chosen_format == "Custom":
                custom_format = st.text_input("Enter custom format (e.g. %d.%m.%Y)", key="dtype_datetime_custom")

            if chosen_format == "Auto (let pandas detect)":
                fmt = None
            elif chosen_format == "Custom":
                fmt = custom_format if custom_format else None
            else:
                fmt = chosen_format

            # Preview
            st.markdown("**Preview (first 8 rows)**")
            if fmt:
                preview_converted = pd.to_datetime(working_df[selected_col].head(8), format=fmt, errors="coerce")
            else:
                preview_converted = pd.to_datetime(working_df[selected_col].head(8), errors="coerce")

            preview_df = pd.DataFrame({
                f"{selected_col} (original)": working_df[selected_col].head(8).values,
                f"{selected_col} (parsed)": preview_converted.values
            })
            st.dataframe(preview_df, use_container_width=True, hide_index=True)

            # Count failures
            if fmt:
                full_converted = pd.to_datetime(working_df[selected_col], format=fmt, errors="coerce")
            else:
                full_converted = pd.to_datetime(working_df[selected_col], errors="coerce")

            original_missing = int(working_df[selected_col].isna().sum())
            new_missing = int(full_converted.isna().sum())
            failed = new_missing - original_missing
            total_non_missing = len(working_df) - original_missing

            if failed > 0:
                if total_non_missing > 0 and failed == total_non_missing:
                    st.error(f"❌ **{selected_col}** cannot be parsed as datetime. All {failed} values failed.")
                    can_apply = False
                else:
                    st.warning(f"⚠️ {failed} value(s) could not be parsed and will become NaT (missing).")
                    can_apply = True
            else:
                can_apply = True

            if can_apply:
                if st.button("Apply Datetime Conversion", key="apply_datetime"):
                    checkpoint_state()
                    working_df[selected_col] = full_converted
                    st.session_state["clean_df"] = working_df
                    
                    log_fmt_detail = fmt
                    if not fmt:
                        sample_val = str(working_df[selected_col].dropna().iloc[0]) if len(working_df[selected_col].dropna()) > 0 else ""
                        if len(sample_val.split("-")) == 3: log_fmt_detail = "Auto-detected (e.g., YYYY-MM-DD)"
                        elif len(sample_val.split("/")) == 3: log_fmt_detail = "Auto-detected (e.g., MM/DD/YYYY)"
                        elif " " in sample_val and ":" in sample_val: log_fmt_detail = "Auto-detected (Timestamp format)"
                        else: log_fmt_detail = "Auto-detected by Pandas"
                    
                    rows_parsed = int((~full_converted.isna()).sum()) - original_missing
                    add_log("Convert to Datetime", {"format": log_fmt_detail}, [selected_col], rows_affected={"rows_converted": max(0, rows_parsed)})
                    st.success(f"Converted '{selected_col}' to datetime.")
                    st.rerun()

    # CONVERT TO CATEGORICAL
    elif selected_tool == "Convert to Categorical":
        st.markdown("### Convert to Categorical")
        st.caption("Convert columns with repeating values to the efficient 'category' dtype.")

        non_cat_cols = [
            c for c in working_df.columns
            if str(working_df[c].dtype) != "category"
        ]
        if not non_cat_cols:
            st.success("All columns are already categorical!")
            return

        selected_cols = st.multiselect("Select columns to convert", non_cat_cols, key="dtype_cat_cols")

        if selected_cols:
            st.markdown("**Column stats**")
            stats_data = []
            for col_name in selected_cols:
                series = working_df[col_name]
                stats_data.append({
                    "Column": col_name,
                    "Current Type": str(series.dtype),
                    "Unique Values": int(series.nunique()),
                    "Total Rows": len(series),
                    "Unique %": round((series.nunique() / max(len(series), 1)) * 100, 2)
                })
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True, hide_index=True)

            for row in stats_data:
                if row["Unique %"] > 80:
                    st.warning(
                        f"⚠️ **{row['Column']}** has {row['Unique %']}% unique values. "
                        f"Converting highly unique columns to categorical may not save memory."
                    )

            if st.button("Apply Categorical Conversion", key="apply_categorical"):
                checkpoint_state()
                for col_name in selected_cols:
                    working_df[col_name] = working_df[col_name].astype("category")
                st.session_state["clean_df"] = working_df
                add_log("Convert to Categorical", {"action": "to_category"}, list(selected_cols), rows_affected={"columns_converted": len(selected_cols)})
                st.success(f"Converted {len(selected_cols)} column(s) to categorical.")
                st.rerun()
