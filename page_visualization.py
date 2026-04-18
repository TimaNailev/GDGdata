import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import streamlit as st
import io
import plotly.express as px
import re
import json
from utils import get_columns_by_type
from ai_assistant import get_viz_suggestions, get_chart_analysis, get_story_contract_interpretation



def show_visualization_builder(active_df):
    st.header("Visualization Builder")

    if active_df is None:
        st.warning("Upload dataset first.")
        return

    # ---------------------------------------------------------
    # CENTRALIZED STATE MANAGEMENT LAYER (Bulletproof Sync)
    # ---------------------------------------------------------
    if "viz_p_config" not in st.session_state:
        st.session_state["viz_p_config"] = {
            "vis_library": "Matplotlib",
            "chart_type": "Scatter Plot",
            "style_title": "My Analysis Chart",
            "style_font": 14,
            "style_font_family": "sans-serif",
            "style_bg": "#ffffff",
            "style_primary_color": "#8DBCC7",
            "style_label_color": "#64748b",
            "style_grid": True,
            "style_leg_orient": "Vertical",
            "style_leg_v": "top",
            "style_leg_h": "right",
            "style_legend": True
        }

    def _sync(key, widget_key=None):
        bk = widget_key if widget_key else key
        if bk in st.session_state:
            st.session_state["viz_p_config"][key] = st.session_state[bk]

    def _get_persistent(key, default):
        return st.session_state["viz_p_config"].get(key, default)

    def _change_lib(new_lib):
        st.session_state["viz_p_config"]["vis_library"] = new_lib
        st.session_state["vis_library"] = new_lib

    # Ensure master vis_library is synced
    if "vis_library" not in st.session_state:
        st.session_state["vis_library"] = _get_persistent("vis_library", "Matplotlib")

    # Use cleaned df if available, otherwise original
    vis_df = st.session_state.get("clean_df")
    if vis_df is None:
        vis_df = active_df
    vis_df = vis_df.copy()
    original_len = len(vis_df)

    st.markdown("Build dynamic charts using the controls on the left. Data used is the current working/cleaned dataset.")

    # -------------------------
    # PREMIUM LIBRARY SELECTION (Stable Callbacks)
    # -------------------------
    st.subheader("Choose Visualization Library")
    lib_cols = st.columns(2)
    curr_lib = st.session_state["vis_library"]
    
    with lib_cols[0]:
        is_mp = curr_lib == "Matplotlib"
        st.button("Matplotlib", on_click=_change_lib, args=("Matplotlib",), use_container_width=True, type="primary" if is_mp else "secondary", key="btn_switch_mp")
        st.caption("Static, clean standard charts. Great for reports.")
        
    with lib_cols[1]:
        is_pl = curr_lib == "Plotly"
        st.button("Plotly", on_click=_change_lib, args=("Plotly",), use_container_width=True, type="primary" if is_pl else "secondary", key="btn_switch_pl")
        st.caption("Interactive, zoomable charts. Great for exploring.")
                
    st.divider()

    # Global Data Filters for Visualization
    with st.expander("🔍 Data Filters (Apply to all charts)", expanded=False):
        st.caption("Filter the dataset before plotting to reduce noise or focus on specific subsets.")
        c1, c2, c3 = st.columns(3)

        # Categorical Filter
        cat_cols_for_filter = [c for c in vis_df.columns if not pd.api.types.is_numeric_dtype(vis_df[c])]
        filter_cat_col = c1.selectbox("Filter by Category", ["(None)"] + cat_cols_for_filter, key="vis_filt_cat_col")
        if filter_cat_col != "(None)":
            unique_cats = vis_df[filter_cat_col].dropna().unique().tolist()
            selected_cats = c1.multiselect("Select values to keep", unique_cats, default=unique_cats, key="vis_filt_cats")
            if selected_cats:
                vis_df = vis_df[vis_df[filter_cat_col].isin(selected_cats)]

        # Numeric Filter
        num_cols_for_filter = [c for c in vis_df.columns if pd.api.types.is_numeric_dtype(vis_df[c])]
        filter_num_col = c2.selectbox("Filter by Numeric Range", ["(None)"] + num_cols_for_filter, key="vis_filt_num_col")
        if filter_num_col != "(None)":
            min_val = float(vis_df[filter_num_col].min())
            max_val = float(vis_df[filter_num_col].max())
            if min_val < max_val:
                selected_range = c2.slider("Select range to keep", min_value=min_val, max_value=max_val, value=(min_val, max_val), key="vis_filt_num_rng")
                vis_df = vis_df[(vis_df[filter_num_col] >= selected_range[0]) & (vis_df[filter_num_col] <= selected_range[1])]

        # Datetime Filter
        dt_cols_for_filter = [c for c in vis_df.columns if pd.api.types.is_datetime64_any_dtype(vis_df[c])]
        filter_dt_col = c3.selectbox("Filter by Date Range", ["(None)"] + dt_cols_for_filter, key="vis_filt_dt_col")
        if filter_dt_col != "(None)":
            min_date = vis_df[filter_dt_col].dropna().min()
            max_date = vis_df[filter_dt_col].dropna().max()
            if pd.notnull(min_date) and pd.notnull(max_date):
                try:
                    min_date_val = min_date.date()
                    max_date_val = max_date.date()
                    if min_date_val < max_date_val:
                        selected_dt_range = c3.slider("Select date range", min_value=min_date_val, max_value=max_date_val, value=(min_date_val, max_date_val), key="vis_filt_dt_rng")
                        vis_df = vis_df[(vis_df[filter_dt_col].dt.date >= selected_dt_range[0]) & (vis_df[filter_dt_col].dt.date <= selected_dt_range[1])]
                except Exception:
                    pass

    filtered_len = len(vis_df)
    st.write(f"**Observations Used:** {filtered_len}  *(Before applying filters: {original_len} | After applying filters: {filtered_len})*")

    @st.dialog("Filtered Data Preview", width="large")
    def show_vis_preview():
        st.caption(f"Previewing the {filtered_len} rows currently filtered for visualization.")
        st.dataframe(vis_df, use_container_width=True)

    if st.button("👀 Preview Filtered Data", use_container_width=False, type="secondary"):
        show_vis_preview()

    st.divider()

    # Captain Price visualization suggestion
    if st.button("🎖️ Ask Captain Price for Chart Suggestions", type="primary"):
        with st.spinner("Captain Price is analyzing your data..."):
            suggestions = get_viz_suggestions(vis_df)
        st.session_state["ai_viz_suggestions"] = suggestions
    if st.session_state.get("ai_viz_suggestions"):
        with st.expander("🎖️ Captain Price’s Chart Recommendations", expanded=True):
            content = st.session_state["ai_viz_suggestions"]
            
            # Improved regex for robustness
            json_match = re.search(r"```json\s*\n?(.*?)\n?```", content, re.DOTALL)
            if json_match:
                try:
                    suggestions = json.loads(json_match.group(1).strip())
                    for i, sug in enumerate(suggestions):
                        st.markdown(f"#### 💡 {sug.get('title', 'Suggestion')}")
                        st.write(sug.get('explanation', ''))
                        
                        c_type = sug.get('chart_type')
                        btn_label = f"🎖️ Create {c_type}"
                        if st.button(btn_label, key=f"create_ai_chart_{i}", type="primary", use_container_width=True):
                            # Ensure chart type matches exactly one of the options
                            valid_types = ["Scatter Plot", "Line Chart", "Bar Chart", "Histogram", "Box Plot", "Heatmap (Correlation)"]
                            matched_type = next((t for t in valid_types if t.lower() in c_type.lower()), c_type)
                            
                            # 1. Set Chart Type
                            st.session_state["chart_type_selector"] = matched_type
                            
                            # 2. Set all parameters
                            params = sug.get("params", {})
                            for k, v in params.items():
                                # Basic validation: only set if key exists in our known set or follows the pattern
                                st.session_state[k] = v
                                
                            # 3. Handle special checks (auto-toggle checkboxes)
                            if "scat_c" in params: st.session_state["scat_c_check"] = True
                            if "line_c" in params: st.session_state["line_c_check"] = True
                            if "box_x" in params: st.session_state["box_grp_check"] = True
                            
                            st.success(f"Configuring {matched_type}... Ready for engagement.")
                            st.rerun()
                        st.divider()
                except Exception as e:
                    st.error(f"Error parsing suggestions: {e}")
                    st.markdown(content)
            else:
                st.markdown(content)
                
                if st.button("Dismiss Suggestions", key="dismiss_viz_sug"):
                    del st.session_state["ai_viz_suggestions"]
                    st.rerun()
    st.divider()

    # -------------------------
    # STORY CONTRACT WORKFLOW
    # -------------------------
    render_story_contract(vis_df)
    st.divider()

    # Setup columns
    ctrl_col, chart_col = st.columns([1, 2.5])

    # 1. CHART TYPE STABILITY
    if "chart_type_selector" not in st.session_state:
        st.session_state["chart_type_selector"] = "Scatter Plot"

    with ctrl_col:
        st.subheader("Chart Configuration")
        
        type_opts = ["Scatter Plot", "Line Chart", "Bar Chart", "Histogram", "Box Plot", "Heatmap (Correlation)"]
        curr_type = _get_persistent("chart_type", "Scatter Plot")
        type_idx = type_opts.index(curr_type) if curr_type in type_opts else 0
        
        def _on_type_change():
            _sync("chart_type", "chart_type_selector")
            _sync_axis_labels()

        chart_type = st.selectbox(
            "Select Chart Type",
            type_opts,
            index=type_idx,
            on_change=_sync, args=("chart_type", "chart_type_selector"),
            key="chart_type_selector"
        )

        # 2. COLUMN & PARAMETER SELECTORS
        num_cols = get_columns_by_type(vis_df, "numeric")
        cat_cols = get_columns_by_type(vis_df, "categorical")
        dt_cols = get_columns_by_type(vis_df, "datetime")

        def _get_idx(key, options, default_idx=0):
            val = st.session_state.get(key)
            if val in options: return options.index(val)
            return min(default_idx, len(options)-1) if options else 0

        # --- AUTO-SYNC LOGIC (Detect Column Changes) ---
        # If the user picks a new column, we FORCE the titles to update
        # regardless of what's in viz_p_config to avoid "frozen" labels.
        c_type_key = st.session_state.get("chart_type_selector", "Scatter Plot")
        prefix = "scat" if c_type_key == "Scatter Plot" else "line" if c_type_key == "Line Chart" else "bar" if c_type_key == "Bar Chart" else "box" if c_type_key == "Box Plot" else "hist"
        
        current_x = st.session_state.get(f"{prefix}_x")
        current_y = st.session_state.get(f"{prefix}_y")
        
        if "last_viz_x" not in st.session_state: st.session_state["last_viz_x"] = {}
        if "last_viz_y" not in st.session_state: st.session_state["last_viz_y"] = {}

        if current_x and st.session_state["last_viz_x"].get(c_type_key) != current_x:
            st.session_state["style_x_title"] = str(current_x)
            st.session_state["viz_p_config"]["style_x_title"] = str(current_x)
            st.session_state["last_viz_x"][c_type_key] = current_x
        
        if current_y and st.session_state["last_viz_y"].get(c_type_key) != current_y:
            st.session_state["style_y_title"] = str(current_y)
            st.session_state["viz_p_config"]["style_y_title"] = str(current_y)
            st.session_state["last_viz_y"][c_type_key] = current_y

        x_col, y_col, color_col, agg_func = None, None, None, None

        if chart_type == "Scatter Plot":
            idx_x = _get_idx("scat_x", num_cols, 0)
            idx_y = _get_idx("scat_y", num_cols, 1)
            
            x_col = st.selectbox("X-Axis (Numeric)", num_cols, index=idx_x, on_change=_sync, args=("scat_x",), key="scat_x") if num_cols else None
            y_col = st.selectbox("Y-Axis (Numeric)", num_cols, index=idx_y, on_change=_sync, args=("scat_y",), key="scat_y") if num_cols else None
            
            sc_checked = _get_persistent("scat_c_check", False)
            if st.checkbox("Add Color Grouping", value=sc_checked, on_change=_sync, args=("scat_c_check",), key="scat_c_check"):
                idx_c = _get_idx("scat_c", cat_cols, 0)
                color_col = st.selectbox("Color By (Categorical)", cat_cols, index=idx_c, on_change=_sync, args=("scat_c",), key="scat_c") if cat_cols else None

        elif chart_type == "Line Chart":
            x_options = dt_cols + num_cols
            idx_x = _get_idx("line_x", x_options, 0)
            idx_y = _get_idx("line_y", num_cols, 0)
            
            x_col = st.selectbox("X-Axis (Time or Numeric)", x_options, index=idx_x, on_change=_sync, args=("line_x",), key="line_x")
            y_col = st.selectbox("Y-Axis (Numeric)", num_cols, index=idx_y, on_change=_sync, args=("line_y",), key="line_y") if num_cols else None
            
            agg_opts = ["mean", "sum", "median", "max", "min", "none (raw)"]
            idx_a = _get_idx("line_agg", agg_opts, 0)
            agg_func = st.selectbox("Aggregation", agg_opts, index=idx_a, on_change=_sync, args=("line_agg",), key="line_agg")

            if x_col in dt_cols:
                t_opts = ["None (Raw Dates)", "Daily (D)", "Weekly (W)", "Monthly (M)", "Quarterly (Q)", "Yearly (Y)", "5 Years (5Y)"]
                idx_t = _get_idx("line_time_agg", t_opts, 0)
                time_agg = st.selectbox("Time Interval Aggregation", t_opts, index=idx_t, on_change=_sync, args=("line_time_agg",), key="line_time_agg")
            else:
                time_agg = "None (Raw Dates)"

            rolling_val = _get_persistent("line_smooth", 1)
            rolling_window = st.slider("Smoothing Window", 1, 100, value=int(rolling_val), on_change=_sync, args=("line_smooth",), key="line_smooth")
            
            lc_checked = _get_persistent("line_c_check", False)
            if st.checkbox("Add Color Grouping", value=lc_checked, on_change=_sync, args=("line_c_check",), key="line_c_check"):
                idx_c = _get_idx("line_c", cat_cols, 0)
                color_col = st.selectbox("Color By (Categorical)", cat_cols, index=idx_c, on_change=_sync, args=("line_c",), key="line_c") if cat_cols else None

        elif chart_type == "Bar Chart":
            idx_x = _get_idx("bar_x", cat_cols, 0)
            x_col = st.selectbox("X-Axis (Categories)", cat_cols, index=idx_x, on_change=_sync, args=("bar_x",), key="bar_x") if cat_cols else None
            y_opts = ["(Count Rows)"] + num_cols
            idx_y = _get_idx("bar_y", y_opts, 0)
            y_col = st.selectbox("Y-Axis (Numeric)", y_opts, index=idx_y, on_change=_sync, args=("bar_y",), key="bar_y")
            if y_col != "(Count Rows)":
                agg_opts = ["sum", "mean", "median", "max", "min"]
                idx_a = _get_idx("bar_agg", agg_opts, 0)
                agg_func = st.selectbox("Aggregation", agg_opts, index=idx_a, on_change=_sync, args=("bar_agg",), key="bar_agg")
            
            top_n_val = _get_persistent("bar_top_n_slider", 20)
            top_n = st.slider("Show Top N categories", 1, 100, value=int(top_n_val), on_change=_sync, args=("bar_top_n_slider",), key="bar_top_n_slider")

        elif chart_type == "Histogram":
            idx_x = _get_idx("hist_x", num_cols, 0)
            x_col = st.selectbox("Column (Numeric)", num_cols, index=idx_x, on_change=_sync, args=("hist_x",), key="hist_x") if num_cols else None
            if x_col:
                hist_bin_val = _get_persistent("hist_bins_slider", 20)
                hist_bins = st.slider("Number of Bins", 5, 100, value=int(hist_bin_val), on_change=_sync, args=("hist_bins_slider",), key="hist_bins_slider")

        elif chart_type == "Box Plot":
            idx_y = _get_idx("box_y", num_cols, 0)
            y_col = st.selectbox("Value Column (Numeric)", num_cols, index=idx_y, on_change=_sync, args=("box_y",), key="box_y") if num_cols else None
            
            bg_checked = _get_persistent("box_grp_check", False)
            if st.checkbox("Group by Category", value=bg_checked, on_change=_sync, args=("box_grp_check",), key="box_grp_check"):
                idx_x = _get_idx("box_x", cat_cols, 0)
                x_col = st.selectbox("Group By (Categorical)", cat_cols, index=idx_x, on_change=_sync, args=("box_x",), key="box_x") if cat_cols else None

        elif chart_type == "Heatmap (Correlation)":
            def_vars = _get_persistent("heat_vars", num_cols[:8])
            y_col = st.multiselect("Select Variables (Numeric)", num_cols, default=def_vars, on_change=_sync, args=("heat_vars",), key="heat_vars")

        def _get_idx(key, options, default_idx=0):
            val = st.session_state.get(key)
            if val in options: return options.index(val)
            return min(default_idx, len(options)-1) if options else 0

        # --- AUTO-SYNC LOGIC (Detect Column Changes) ---
        # If the user picks a new column, we FORCE the titles to update
        # regardless of what's in viz_p_config to avoid "frozen" labels.
        c_type_key = st.session_state.get("chart_type_selector", "Scatter Plot")
        prefix = "scat" if c_type_key == "Scatter Plot" else "line" if c_type_key == "Line Chart" else "bar" if c_type_key == "Bar Chart" else "box" if c_type_key == "Box Plot" else "hist"
        
        current_x = st.session_state.get(f"{prefix}_x")
        current_y = st.session_state.get(f"{prefix}_y")
        
        if "last_viz_x" not in st.session_state: st.session_state["last_viz_x"] = {}
        if "last_viz_y" not in st.session_state: st.session_state["last_viz_y"] = {}

        if current_x and st.session_state["last_viz_x"].get(c_type_key) != current_x:
            st.session_state["viz_p_config"]["style_x_title"] = str(current_x)
            st.session_state["last_viz_x"][c_type_key] = current_x
        
        if current_y and st.session_state["last_viz_y"].get(c_type_key) != current_y:
            st.session_state["viz_p_config"]["style_y_title"] = str(current_y)
            st.session_state["last_viz_y"][c_type_key] = current_y

        # Auto-update chart title if it's still generic/default
        curr_title = st.session_state.get("style_title", "")
        if not curr_title or curr_title in ["My Analysis Chart", "Scatter Plot", "Line Chart", "Bar Chart", "Histogram", "Box Plot"] or "vs" in curr_title:
            if current_x and current_y: t = f"{current_y} vs {current_x}"
            elif current_x: t = f"Distribution of {current_x}"
            else: t = f"{c_type_key} Analysis"
            st.session_state["viz_p_config"]["style_title"] = t
            st.session_state["style_title"] = t

        st.divider(); st.divider(); st.subheader("🎨 Style & Branding")
        
        # --- GLOBAL STYLE INITIALIZATION (Bulletproof Parity) ---
        # We define these BEFORE the tabs so they are always available to the chart rendering logic
        chart_title = _get_persistent("style_title", f"{chart_type}")
        font_size = _get_persistent("style_font", 14)
        font_family = _get_persistent("style_font_family", "sans-serif")
        bg_color = _get_persistent("style_bg", "#ffffff")
        primary_color = _get_persistent("style_primary_color", "#1f77b4")
        
        # Axis Titles: Default to column names if not and override with persistence
        # Note: persistence now includes the auto-sync values updated above
        x_default = str(current_x) if current_x else ""
        y_default = "Rows Count" if current_y == "(Count Rows)" else str(current_y) if current_y else ""
        
        x_title = _get_persistent("style_x_title", x_default)
        y_title = _get_persistent("style_y_title", y_default)
        
        x_rot = _get_persistent("style_x_rot", 45 if chart_type == "Bar Chart" else 0)
        y_rot = _get_persistent("style_y_rot", 0)
        label_color = _get_persistent("style_label_color", "#333333")
        show_grid = _get_persistent("style_grid", True)
        
        # Legend
        show_legend = _get_persistent("style_legend", True)
        l_orient = _get_persistent("style_leg_orient", "Vertical")
        l_pos_v = _get_persistent("style_leg_v", "top")
        l_pos_h = _get_persistent("style_leg_h", "right")

        # Trace properties
        t_size = _get_persistent("style_size", 8)
        line_dash = _get_persistent("style_dash", "solid")
        marker_symbol = _get_persistent("style_symbol", "circle")
        bar_gap = _get_persistent("style_bar_gap", 0.2)

        # Tabs for UI only - They now purely control st.session_state via callbacks
        style_tabs = st.tabs(["General", "Axes", "Traces", "Legend"])

        with style_tabs[0]: # GENERAL
            st.text_input("Chart Title", value=chart_title, on_change=_sync, args=("style_title",), key="style_title")
            st.slider("Base Font Size", 8, 36, value=int(font_size), on_change=_sync, args=("style_font",), key="style_font")
            f_opts = ["sans-serif", "serif", "monospace", "Arial", "Courier New", "Verdana"]
            idx_f = _get_idx("style_font_family", f_opts, 0)
            st.selectbox("Font Family", f_opts, index=idx_f, on_change=_sync, args=("style_font_family",), key="style_font_family")
            st.color_picker("Background Color", value=bg_color, on_change=_sync, args=("style_bg",), key="style_bg")
            st.color_picker("Primary Color", value=primary_color, on_change=_sync, args=("style_primary_color",), key="style_primary_color")

        with style_tabs[1]: # AXES
            st.text_input("X-Axis Title", value=x_title, on_change=_sync, args=("style_x_title",), key="style_x_title")
            st.text_input("Y-Axis Title", value=y_title, on_change=_sync, args=("style_y_title",), key="style_y_title")
            
            c1, c2 = st.columns(2)
            rot_opts = [0, 45, 90]
            idx_rx = _get_idx("style_x_rot", rot_opts, 1 if chart_type == "Bar Chart" else 0)
            idx_ry = _get_idx("style_y_rot", rot_opts, 0)
            c1.selectbox("X-Label Rotation", rot_opts, index=idx_rx, on_change=_sync, args=("style_x_rot",), key="style_x_rot")
            c2.selectbox("Y-Label Rotation", rot_opts, index=idx_ry, on_change=_sync, args=("style_y_rot",), key="style_y_rot")
            st.color_picker("Axis Label Color", value=label_color, on_change=_sync, args=("style_label_color",), key="style_label_color")
            st.toggle("Show Grid Lines", value=show_grid, on_change=_sync, args=("style_grid",), key="style_grid")

        with style_tabs[2]: # TRACES
            st.caption("Marker and Line Properties")
            if chart_type in ["Line Chart", "Scatter Plot"]:
                t_c1, t_c2 = st.columns(2)
                t_c1.slider("Line Width / Marker Size", 1, 30, value=int(t_size), on_change=_sync, args=("style_size",), key="style_size")
                if chart_type == "Line Chart":
                    d_opts = ["solid", "dot", "dash", "longdash"]
                    idx_d = _get_idx("style_dash", d_opts, 0)
                    st.selectbox("Line Dash", d_opts, index=idx_d, on_change=_sync, args=("style_dash",), key="style_dash")
                else: 
                    s_opts = ["circle", "square", "diamond", "cross", "x"]
                    idx_s = _get_idx("style_symbol", s_opts, 0)
                    st.selectbox("Marker Shape", s_opts, index=idx_s, on_change=_sync, args=("style_symbol",), key="style_symbol")
            elif chart_type == "Bar Chart":
                st.slider("Gap Between Bars", 0.0, 0.5, value=float(bar_gap), step=0.05, on_change=_sync, args=("style_bar_gap",), key="style_bar_gap")

            # DYNAMIC MULTI-COLOR HANDLER
            rep_groups = []
            if color_col:
                rep_groups = list(vis_df[color_col].dropna().unique())
            elif chart_type == "Box Plot" and x_col:
                rep_groups = list(vis_df[x_col].dropna().unique())
            elif chart_type == "Bar Chart" and x_col:
                if y_col == "(Count Rows)":
                    rep_groups = list(vis_df[x_col].value_counts().head(top_n).index)
                else:
                    try:
                        safe_agg = agg_func if agg_func in ["sum", "mean", "median", "max", "min"] else "sum"
                        if pd.api.types.is_numeric_dtype(vis_df[y_col]):
                            rep_groups = list(vis_df.groupby(x_col)[y_col].agg(safe_agg).sort_values(ascending=False).head(top_n).index)
                        else:
                            rep_groups = list(vis_df[x_col].value_counts().head(top_n).index)
                    except:
                        rep_groups = list(vis_df[x_col].value_counts().head(top_n).index)

            if "viz_custom_colors" not in st.session_state: st.session_state["viz_custom_colors"] = {}
            custom_colors = {}
            if rep_groups:
                st.markdown("**Individual Series Colors**")
                for i, group in enumerate(rep_groups[:20]):
                    g_str = str(group)
                    default_c = st.session_state["viz_custom_colors"].get(g_str)
                    if not default_c:
                        default_c = ["#8DBCC7", "#A4CCD9", "#C4E1E6", "#EBFFD8", "#64748b", "#94a3b8", "#e2e8f0", "#334155", "#1e293b", "#0f172a"][i % 10]
                    picked_color = st.color_picker(f"Color: {g_str}", value=default_c, key=f"picker_{g_str}")
                    st.session_state["viz_custom_colors"][g_str] = picked_color
                    custom_colors[g_str] = picked_color
            else:
                custom_colors = None

        with style_tabs[3]: # LEGEND
            st.checkbox("Show Legend", value=show_legend, on_change=_sync, args=("style_legend",), key="style_legend")
            o_opts = ["Vertical", "Horizontal"]
            idx_o = _get_idx("style_leg_orient", o_opts, 0)
            st.selectbox("Orientation", o_opts, index=idx_o, on_change=_sync, args=("style_leg_orient",), key="style_leg_orient")
            v_opts = ["top", "middle", "bottom"]
            idx_v = _get_idx("style_leg_v", v_opts, 0)
            st.selectbox("Vertical Position", v_opts, index=idx_v, on_change=_sync, args=("style_leg_v",), key="style_leg_v")
            h_opts = ["left", "center", "right"]
            idx_h = _get_idx("style_leg_h", h_opts, 2)
            st.selectbox("Horizontal Position", h_opts, index=idx_h, on_change=_sync, args=("style_leg_h",), key="style_leg_h")

    with chart_col:
        # Check numeric requirements
        if (chart_type in ["Scatter Plot", "Histogram", "Box Plot"] and not num_cols) or (chart_type == "Heatmap (Correlation)" and len(num_cols) < 2):
            st.warning("Not enough numeric columns available for this chart type.")
        else:
            vis_lib = st.session_state.get("vis_library", "Matplotlib")
            
            if vis_lib == "Matplotlib":
                try:
                    fig, ax = plt.subplots(figsize=(12, 7))
                    fig.patch.set_facecolor(bg_color)
                    ax.set_facecolor(bg_color)
                    
                    # Font setup
                    plt.rcParams.update({
                        'font.size': font_size,
                        'font.family': font_family
                    })

                    # Marker Map
                    m_map = {"circle": "o", "square": "s", "diamond": "D", "cross": "P", "x": "X"}
                    m_curr = m_map.get(marker_symbol, "o")

                    # Plot logic
                    if chart_type == "Scatter Plot" and x_col and y_col:
                        if color_col:
                            for group, data in vis_df.groupby(color_col):
                                c = custom_colors.get(str(group), primary_color) if custom_colors else primary_color
                                ax.scatter(data[x_col].astype(float), data[y_col].astype(float), label=str(group), s=t_size*10, alpha=0.7, color=c, marker=m_curr)
                        else:
                            ax.scatter(vis_df[x_col].astype(float), vis_df[y_col].astype(float), color=primary_color, s=t_size*10, alpha=0.7, marker=m_curr)

                    elif chart_type == "Line Chart" and x_col and y_col:
                        # Execute time aggregation logic
                        if time_agg != "None (Raw Dates)":
                            freq_map = {"Daily (D)": "D", "Weekly (W)": "W", "Monthly (M)": "ME", "Quarterly (Q)": "QE", "Yearly (Y)": "YE", "5 Years (5Y)": "5YE"}
                            freq = freq_map.get(time_agg, "D")
                            chosen_agg = agg_func if agg_func != "none (raw)" else "mean"
                            if color_col:
                                plot_df = vis_df.set_index(x_col).groupby(color_col).resample(freq)[y_col].agg(chosen_agg).reset_index()
                            else:
                                plot_df = vis_df.set_index(x_col).resample(freq)[y_col].agg(chosen_agg).reset_index()
                            plot_df = plot_df.dropna(subset=[y_col])
                        else:
                            if agg_func != "none (raw)":
                                if color_col:
                                    plot_df = vis_df.groupby([x_col, color_col], as_index=False)[y_col].agg(agg_func)
                                else:
                                    plot_df = vis_df.groupby(x_col, as_index=False)[y_col].agg(agg_func)
                            else:
                                plot_df = vis_df.copy()

                        plot_df = plot_df.sort_values(by=x_col)
                        if color_col:
                            for group, data in plot_df.groupby(color_col):
                                y_data = data[y_col].astype(float)
                                if rolling_window > 1: y_data = y_data.rolling(window=rolling_window, min_periods=1).mean()
                                c = custom_colors.get(str(group), primary_color) if custom_colors else primary_color
                                ax.plot(data[x_col].astype(str), y_data, label=str(group), linewidth=t_size/4, color=c, linestyle=line_dash.replace('longdash','--').replace('dash','--').replace('dot',':'))
                        else:
                            y_data = plot_df[y_col].astype(float)
                            if rolling_window > 1: y_data = y_data.rolling(window=rolling_window, min_periods=1).mean()
                            ax.plot(plot_df[x_col].astype(str), y_data, color=primary_color, linewidth=t_size/4, linestyle=line_dash.replace('longdash','--').replace('dash','--').replace('dot',':'))

                    elif chart_type == "Bar Chart" and x_col:
                        if y_col == "(Count Rows)":
                            vc = vis_df[x_col].value_counts().head(top_n)
                            labels = [str(i) for i in vc.index]
                            colors = [custom_colors.get(l, primary_color) for l in labels] if custom_colors else primary_color
                            ax.bar(labels, vc.values.astype(float), color=colors)
                        else:
                            grouped = vis_df.groupby(x_col)[y_col].agg(agg_func).sort_values(ascending=False).head(top_n)
                            labels = [str(i) for i in grouped.index]
                            colors = [custom_colors.get(l, primary_color) for l in labels] if custom_colors else primary_color
                            ax.bar(labels, grouped.values.astype(float), color=colors)

                    elif chart_type == "Histogram" and x_col:
                        ax.hist(vis_df[x_col].dropna().astype(float), bins=hist_bins, color=primary_color, edgecolor='black', alpha=0.7)

                    elif chart_type == "Box Plot" and y_col:
                        if x_col:
                            labels, data_vals = [], []
                            for g_name, g_data in vis_df.groupby(x_col):
                                valid = g_data[y_col].dropna().astype(float).values
                                if len(valid) > 0:
                                    labels.append(str(g_name))
                                    data_vals.append(valid)
                            if data_vals:
                                bplot = ax.boxplot(data_vals, labels=labels, patch_artist=True)
                                for i, patch in enumerate(bplot['boxes']):
                                    c = custom_colors.get(labels[i], primary_color) if custom_colors else primary_color
                                    patch.set_facecolor(c)
                        else:
                            bplot = ax.boxplot(vis_df[y_col].dropna().astype(float), patch_artist=True)
                            for patch in bplot['boxes']: patch.set_facecolor(primary_color)

                    elif chart_type == "Heatmap (Correlation)":
                        vars_to_corr = y_col
                        if vars_to_corr and len(vars_to_corr) > 1:
                            corr = vis_df[vars_to_corr].corr()
                            sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax, fmt=".2f", center=0)

                    # Final Styling
                    ax.set_title(chart_title, pad=20, fontsize=font_size+6, color=label_color)
                    ax.set_xlabel(x_title, color=label_color)
                    ax.set_ylabel(y_title, color=label_color)
                    ax.tick_params(axis='x', rotation=x_rot, colors=label_color)
                    ax.tick_params(axis='y', rotation=y_rot, colors=label_color)
                    if show_grid: ax.grid(True, linestyle='--', alpha=0.3)
                    
                    if show_legend:
                        loc_map = {"top": "upper center", "middle": "center", "bottom": "lower center"}
                        h_loc = "right" if l_pos_h == "right" else "left" if l_pos_h == "left" else "center"
                        v_loc = "upper" if l_pos_v == "top" else "lower" if l_pos_v == "bottom" else "center"
                        final_loc = f"{v_loc} {h_loc}" if v_loc != h_loc else v_loc
                        ax.legend(loc="best" if l_pos_v == "middle" else final_loc, ncols=4 if l_orient == "Horizontal" else 1)

                    st.pyplot(fig, clear_figure=False)
                except Exception as e:
                    st.error(f"Matplotlib Error: {str(e)}")

            elif vis_lib == "Plotly":
                try:
                    fig = None
                    color_map = custom_colors if custom_colors else None
                    
                    if chart_type == "Scatter Plot" and x_col and y_col:
                        fig = px.scatter(vis_df, x=x_col, y=y_col, color=color_col if color_col else None,
                                        title=chart_title, color_discrete_map=color_map, color_discrete_sequence=["#4988C4", "#1C4D8D", "#BDE8F5", "#0F2854"])
                        if not color_col: fig.update_traces(marker=dict(color=primary_color))
                        fig.update_traces(marker=dict(size=t_size, symbol=marker_symbol))

                    elif chart_type == "Line Chart" and x_col and y_col:
                        # Plotly Line Aggregation
                        if time_agg != "None (Raw Dates)":
                            freq_map = {"Daily (D)": "D", "Weekly (W)": "W", "Monthly (M)": "ME", "Quarterly (Q)": "QE", "Yearly (Y)": "YE", "5 Years (5Y)": "5YE"}
                            freq = freq_map.get(time_agg, "D")
                            chosen_agg = agg_func if agg_func != "none (raw)" else "mean"
                            if color_col:
                                plot_df = vis_df.set_index(x_col).groupby(color_col).resample(freq)[y_col].agg(chosen_agg).reset_index()
                            else:
                                plot_df = vis_df.set_index(x_col).resample(freq)[y_col].agg(chosen_agg).reset_index()
                            plot_df = plot_df.dropna(subset=[y_col])
                        else:
                            if agg_func != "none (raw)":
                                if color_col:
                                    plot_df = vis_df.groupby([x_col, color_col], as_index=False)[y_col].agg(agg_func)
                                else:
                                    plot_df = vis_df.groupby(x_col, as_index=False)[y_col].agg(agg_func)
                            else:
                                plot_df = vis_df.copy()

                        plot_df = plot_df.sort_values(by=x_col)
                        if rolling_window > 1:
                            if color_col:
                                plot_df[y_col] = plot_df.groupby(color_col)[y_col].transform(lambda x: x.rolling(window=rolling_window, min_periods=1).mean())
                            else:
                                plot_df[y_col] = plot_df[y_col].rolling(window=rolling_window, min_periods=1).mean()
                                
                        fig = px.line(plot_df, x=x_col, y=y_col, color=color_col if color_col else None, title=chart_title, color_discrete_map=color_map, color_discrete_sequence=["#4988C4", "#1C4D8D", "#BDE8F5", "#0F2854"])
                        if not color_col: fig.update_traces(line=dict(color=primary_color))
                        fig.update_traces(line=dict(width=max(1, t_size//4), dash=line_dash))

                    elif chart_type == "Bar Chart" and x_col:
                        if y_col == "(Count Rows)":
                            vc = vis_df[x_col].value_counts().head(top_n)
                            plot_df = vc.reset_index(); plot_df.columns = [x_col, 'Count']
                            fig = px.bar(plot_df, x=x_col, y='Count', title=chart_title, color=x_col, color_discrete_map=color_map if color_map else None, color_discrete_sequence=["#4988C4", "#1C4D8D", "#BDE8F5", "#0F2854"])
                        else:
                            grouped = vis_df.groupby(x_col)[y_col].agg(agg_func).sort_values(ascending=False).head(top_n)
                            plot_df = grouped.reset_index()
                            fig = px.bar(plot_df, x=x_col, y=y_col, title=chart_title, color=x_col, color_discrete_map=color_map if color_map else None, color_discrete_sequence=["#4988C4", "#1C4D8D", "#BDE8F5", "#0F2854"])
                        if not color_map: fig.update_traces(marker_color=primary_color)
                        fig.update_layout(bargap=bar_gap)

                    elif chart_type == "Histogram" and x_col:
                        fig = px.histogram(vis_df, x=x_col, nbins=hist_bins, title=chart_title, color_discrete_sequence=[primary_color])

                    elif chart_type == "Box Plot" and y_col:
                        fig = px.box(vis_df, x=x_col if x_col else None, y=y_col, title=chart_title, color=x_col if x_col else None, color_discrete_map=color_map if color_map and x_col else None, color_discrete_sequence=["#4988C4", "#1C4D8D", "#BDE8F5", "#0F2854"])
                        if not color_map or not x_col: fig.update_traces(marker_color=primary_color)

                    elif chart_type == "Heatmap (Correlation)":
                        vars_to_corr = y_col
                        if vars_to_corr and len(vars_to_corr) > 1:
                            corr = vis_df[vars_to_corr].corr()
                            fig = px.imshow(corr, text_auto=".2f", aspect="auto", title=chart_title, color_continuous_scale="RdBu_r")

                    if fig:
                        plotly_leg_orient = "h" if l_orient == "Horizontal" else "v"
                        ly = 1.15 if l_pos_v == "top" else 0.5 if l_pos_v == "middle" else -0.2
                        lx = 0 if l_pos_h == "left" else 0.5 if l_pos_h == "center" else 1.0
                        
                        fig.update_layout(
                            font={"size": font_size, "family": font_family},
                            showlegend=show_legend,
                            plot_bgcolor=bg_color, paper_bgcolor=bg_color,
                            legend={"orientation": plotly_leg_orient, "yanchor": "auto", "y": ly, "xanchor": "auto", "x": lx},
                            title={"text": chart_title, "font": {"size": font_size+8, "family": font_family}, "x": 0.5, "xanchor": 'center'}
                        )
                        fig.update_xaxes(title_text=x_title, tickangle=x_rot, tickfont={"color": label_color, "size": font_size}, title_font={"color": label_color, "size": font_size+2}, showgrid=show_grid)
                        fig.update_yaxes(title_text=y_title, tickangle=y_rot, tickfont={"color": label_color, "size": font_size}, title_font={"color": label_color, "size": font_size+2}, showgrid=show_grid)
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Plotly Error: {str(e)}")

            # --- DOWNLOAD CHART DIALOG ---
            if 'fig' in locals() and fig is not None:
                st.divider()
                
                @st.dialog("Download Chart", width="large")
                def show_download_dialog(fig_to_download, is_plotly):
                    st.write("### Preview:")
                    if is_plotly:
                        st.plotly_chart(fig_to_download, use_container_width=True)
                    else:
                        st.pyplot(fig_to_download, clear_figure=False)
                        
                    st.divider()
                    
                    c1, c2 = st.columns(2)
                    file_name = c1.text_input("Chart Name", value="my_chart")
                    
                    options = ["html", "png", "jpeg", "pdf"] if is_plotly else ["png", "jpeg", "pdf"]
                    file_type = c2.selectbox("File Type", options)
                    
                    buf = io.BytesIO()
                    success = False
                    
                    try:
                        if is_plotly:
                            if file_type == "html":
                                # Export as an interactive web page
                                html_str = fig_to_download.to_html(include_plotlyjs="cdn", full_html=True)
                                buf.write(html_str.encode("utf-8"))
                            else:
                                # Plotly requires kaleido to write static images
                                fig_to_download.write_image(buf, format=file_type)
                        else:
                            fig_to_download.savefig(buf, format=file_type, bbox_inches="tight")
                        success = True
                    except Exception as e:
                        st.error(f"Failed to generate file. ({str(e)})")
                        if is_plotly and "kaleido" in str(e).lower() or "requires the kaleido" in str(e).lower():
                            st.info("To download Plotly charts as static images, please run: `pip install kaleido` in your terminal.")
                            
                    if success:
                        mime_dict = {
                            "png": "image/png",
                            "jpeg": "image/jpeg",
                            "pdf": "application/pdf",
                            "html": "text/html"
                        }
                        st.download_button(
                            label=f"⬇️ Download as .{file_type.upper()}",
                            data=buf.getvalue(),
                            file_name=f"{file_name}.{file_type}",
                            mime=mime_dict.get(file_type, "application/octet-stream"),
                            use_container_width=True,
                            type="primary"
                        )

                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("📊 Analyze Chart (AI)", use_container_width=True):
                        with st.spinner("Captain Price is analyzing this chart..."):
                            analysis = get_chart_analysis(
                                vis_df, chart_type,
                                x_col=x_col, y_col=y_col if not isinstance(y_col, list) else str(y_col),
                                color_col=color_col
                            )
                        st.session_state["ai_chart_analysis"] = analysis
                with col2:
                    if st.button("💾 Export / Download Chart", use_container_width=True):
                        show_download_dialog(fig, vis_lib == "Plotly")

                if st.session_state.get("ai_chart_analysis"):
                    st.markdown("---")
                    st.markdown("🎖️ **Captain Price’s Chart Analysis:**")
                    st.markdown(st.session_state["ai_chart_analysis"])
                    if st.button("Dismiss Analysis", key="dismiss_chart_analysis"):
                        del st.session_state["ai_chart_analysis"]
                        st.rerun()


def render_story_contract(df: pd.DataFrame):
    """Renders the Story Contract interface and handles the AI interpretation workflow."""
    if "show_story_contract" not in st.session_state:
        st.session_state.show_story_contract = False
    
    # Story Contract Toggle
    label = "🔼 Close Story Contract" if st.session_state.show_story_contract else "📜 Story Contract"
    if st.button(label, use_container_width=True, type="secondary" if st.session_state.show_story_contract else "primary"):
        st.session_state.show_story_contract = not st.session_state.show_story_contract
        st.rerun()

    if not st.session_state.show_story_contract:
        return

    st.info("🎯 **Build your story.** Define your objectives manually, and Captain Price will interpret the technical requirements.")

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        goal = c1.text_input("Goal", help="What are you trying to achieve?", key="sc_goal")
        audience = c2.text_input("Audience", help="Who is this for?", key="sc_audience")
        question = c3.text_input("Key Question", help="What specific question does this answer?", key="sc_question")

        c4, c5, c6 = st.columns(3)
        metric = c4.text_input("Metric / KPI", help="What are we measuring?", key="sc_metric")
        comparison = c5.text_input("Comparison Dimension", help="What are we comparing against?", key="sc_comp")
        time_dim = c6.text_input("Time Dimension", help="Is there a time aspect?", key="sc_time")

        c7, c8, c9 = st.columns(3)
        filters = c7.text_input("Filters / Focus", help="Any specific subsets?", key="sc_filter")
        pref_chart = c8.text_input("Preferred Chart", help="Any specific style in mind?", key="sc_pref")
        notes = c9.text_area("Notes / Context", help="Any other details?", key="sc_notes")

        # -----------------------------
        # STEP 1: INTERPRET
        # -----------------------------
        if st.button("🎖️ Interpret Story Contract", type="primary", use_container_width=True):
            inputs = {
                "Goal": goal, "Audience": audience, "Key Question": question,
                "Metric": metric, "Comparison": comparison, "Time": time_dim,
                "Filters": filters, "Preferred": pref_chart, "Notes": notes
            }
            with st.spinner("Captain Price is interpreting your mission..."):
                response = get_story_contract_interpretation(df, inputs)
                # Parse JSON
                json_match = re.search(r"```json\s*\n?(.*?)\n?```", response, re.DOTALL)
                if json_match:
                    try:
                        st.session_state["sc_interpretation"] = json.loads(json_match.group(1).strip())
                    except:
                        st.session_state["sc_interpretation"] = response
                else:
                    st.session_state["sc_interpretation"] = response
            st.rerun()

    # -----------------------------
    # STEP 2: DISPLAY INTERPRETATION
    # -----------------------------
    interpretation = st.session_state.get("sc_interpretation")
    if interpretation:
        st.markdown("### 🎖️ Captain Price's Technical Interpretation")
        
        if isinstance(interpretation, dict):
            with st.container(border=True):
                st.markdown(f"#### 📊 Recommended: {interpretation.get('recommended_chart_type')}")
                st.write(interpretation.get('explanation', ''))
                
                ic1, ic2 = st.columns(2)
                all_cols = list(df.columns)
                y_opts = ["(Count Rows)"] + all_cols
                g_opts = ["None"] + all_cols

                def _get_idx_sc(val, opts, default=0):
                    if val in opts: return opts.index(val)
                    return default

                with ic1:
                    st.markdown("**Structural Mapping (Verify/Correct):**")
                    x_val = st.selectbox("X-Axis", all_cols, index=_get_idx_sc(interpretation.get('x_axis'), all_cols), key="sc_override_x")
                    y_val = st.selectbox("Y-Axis", y_opts, index=_get_idx_sc(interpretation.get('y_axis'), y_opts), key="sc_override_y")
                    g_val = st.selectbox("Grouping", g_opts, index=_get_idx_sc(interpretation.get('group_by'), g_opts, 0), key="sc_override_g")
                    
                    # Update interpretation dict with current selectbox values
                    interpretation['x_axis'] = x_val
                    interpretation['y_axis'] = y_val
                    interpretation['group_by'] = g_val if g_val != "None" else None
                    
                    st.write(f"- **Aggregation:** `{interpretation.get('aggregation')}`")

                with ic2:
                    st.markdown("**Narrative:**")
                    st.write(f"- **Suggested Title:** {interpretation.get('title')}")
                    if interpretation.get('assumptions'):
                        st.caption(f"🛡️ Assumptions: {', '.join(interpretation.get('assumptions'))}")
                    if interpretation.get('warnings'):
                        st.warning(f"⚠️ {', '.join(interpretation.get('warnings'))}")

                st.divider()
                st.write("Ready to proceed with this configuration?")
                
                if st.button("🚀 Continue and Create Chart", type="primary", use_container_width=True):
                    apply_story_contract_to_viz(interpretation, df)
                    st.success("Tactical settings applied. Engaging chart.")
                    del st.session_state["sc_interpretation"]
                    st.rerun()
        else:
            st.write(interpretation)
            
        if st.button("Cancel Story Contract"):
            del st.session_state["sc_interpretation"]
            st.rerun()


def apply_story_contract_to_viz(data: dict, df: pd.DataFrame):
    """Maps the AI's interpreted JSON to the application's internal viz_p_config."""
    c_type = data.get("recommended_chart_type", "Scatter Plot")
    
    # 1. Update master selector
    valid_types = ["Scatter Plot", "Line Chart", "Bar Chart", "Histogram", "Box Plot", "Heatmap (Correlation)"]
    matched_type = next((t for t in valid_types if t.lower() in c_type.lower()), "Scatter Plot")
    
    st.session_state["chart_type_selector"] = matched_type
    st.session_state["viz_p_config"]["chart_type"] = matched_type
    
    # 2. Validate columns
    x_col = data.get("x_axis")
    y_col = data.get("y_axis")
    g_col = data.get("group_by")
    agg = data.get("aggregation", "mean")
    title = data.get("title", "My Analysis")
    
    def validate(c):
        return c if c in df.columns or c == "(Count Rows)" else None

    # 3. Apply settings based on type
    if matched_type == "Scatter Plot":
        st.session_state["scat_x"] = validate(x_col)
        st.session_state["scat_y"] = validate(y_col)
        if g_col and g_col in df.columns:
            st.session_state["scat_c_check"] = True
            st.session_state["scat_c"] = g_col
        else:
            st.session_state["scat_c_check"] = False

    elif matched_type == "Line Chart":
        st.session_state["line_x"] = validate(x_col)
        st.session_state["line_y"] = validate(y_col)
        st.session_state["line_agg"] = agg if agg != "none (raw)" else "mean"
        if g_col and g_col in df.columns:
            st.session_state["line_c_check"] = True
            st.session_state["line_c"] = g_col
        else:
            st.session_state["line_c_check"] = False

    elif matched_type == "Bar Chart":
        st.session_state["bar_x"] = validate(x_col)
        st.session_state["bar_y"] = validate(y_col)
        # Bar Chart MUST have a valid aggregation if numeric
        st.session_state["bar_agg"] = agg if agg in ["sum", "mean", "median", "max", "min"] else "sum"

    elif matched_type == "Histogram":
        st.session_state["hist_x"] = validate(x_col)

    elif matched_type == "Box Plot":
        st.session_state["box_y"] = validate(y_col)
        if x_col and x_col in df.columns:
            st.session_state["box_grp_check"] = True
            st.session_state["box_x"] = x_col
        else:
            st.session_state["box_grp_check"] = False

    # 4. Global styles
    st.session_state["style_title"] = title
    st.session_state["style_x_title"] = str(x_col) if x_col else ""
    st.session_state["style_y_title"] = str(y_col) if y_col else ""
    # Store in config as well
    st.session_state["viz_p_config"]["style_title"] = title
    st.session_state["viz_p_config"]["style_x_title"] = st.session_state["style_x_title"]
    st.session_state["viz_p_config"]["style_y_title"] = st.session_state["style_y_title"]
    
    # Reset rotation if it's likely to overlap
    st.session_state["style_x_rot"] = 45 if matched_type == "Bar Chart" else 0
    st.session_state["viz_p_config"]["style_x_rot"] = st.session_state["style_x_rot"]

    # Force sync
    st.session_state["viz_p_config"]["chart_type"] = matched_type
