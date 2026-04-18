import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Set global matplotlib style to match palette
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=['#8DBCC7', '#A4CCD9', '#C4E1E6', '#EBFFD8'])
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['axes.edgecolor'] = '#e2e8f0'
plt.rcParams['axes.labelcolor'] = '#64748b'
plt.rcParams['xtick.color'] = '#64748b'
plt.rcParams['ytick.color'] = '#64748b'
plt.rcParams['text.color'] = '#334155'
plt.rcParams['font.family'] = 'sans-serif'

# =========================
# MODULE IMPORTS
# =========================
from loaders import load_uploaded_file, load_google_sheet
from page_overview import show_interactive_column_overview
from page_visualization import show_visualization_builder
from page_export import show_export_page
from clean_missing import show_missing_values_cleaning
from clean_duplicates import show_duplicates_cleaning
from clean_datatypes import show_data_types_cleaning
from clean_categorical import show_categorical_tools
from clean_numeric import show_numeric_cleaning, show_normalization_scaling
from clean_columns import show_column_operations
from clean_validation import show_data_validation
from clean_reshape import show_reshape_tools
from clean_anonymize import show_anonymization_cleaning
from ai_assistant import (
    render_toggle, render_chat_panel,
    build_dataset_context, build_cleaning_context, build_viz_context,
    get_cleaning_suggestions, get_viz_suggestions,
)
from page_ai_report import show_ai_financial_report


# =========================
# APP PAGES
# =========================
PAGES = [
    "Upload & Overview",
    "AI Financial Management Report",
    "Cleaning & Preparation Studio",
    "Visualization Builder",
    "Export & Report"
]

if "current_page" not in st.session_state:
    st.session_state.current_page = "Upload & Overview"

st.set_page_config(
    page_title="Call of Data | AI Financial Reporting",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Main Content Area */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1200px !important;
        margin: 0 auto !important;
    }

    /* Custom Components Color Palette (Muted Dark Theme) */
    :root {
        /* Standard theme colors are handled natively by .streamlit/config.toml */
        --primary-color: #4988C4;
        --done-color: #10b981;
        --pending-color: #334155; /* Muted dark gray for inactive stepper */
        --text-muted: #94a3b8;
    }

    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Stepper Container */
    .stepper-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        padding: 0 1rem;
        position: relative;
    }

    .stepper-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
        z-index: 1;
    }

    /* Stepper Circle */
    .step-counter {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--pending-color);
        display: flex;
        justify-content: center;
        align-items: center;
        font-weight: bold;
        margin-bottom: 6px;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        color: var(--text-muted);
    }

    .step-counter.active {
        background: var(--primary-color);
        color: white;
        box-shadow: 0 0 15px rgba(141, 188, 199, 0.4);
        transform: scale(1.1);
    }

    .step-counter.done {
        background: var(--done-color);
        color: white;
    }

    /* Stepper Label */
    .step-name {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-muted);
        text-align: center;
    }

    .step-name.active {
        color: var(--primary-color);
        font-weight: 700;
    }

    .step-name.done {
        color: var(--done-color);
    }

    .stepper-line {
        position: absolute;
        top: 20px;
        left: 10%;
        width: 80%;
        height: 2px;
        background: var(--pending-color);
        opacity: 0.5;
        z-index: 0;
    }

    /* Sidebar and Buttons */
    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
    }

    div.stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    /* Primary buttons */
    div.stButton > button[kind="primary"] {
        background-color: var(--primary-color) !important;
        border-color: var(--primary-color) !important;
        color: white !important;
    }

    div.stButton > button[kind="secondary"]:hover {
        border-color: var(--primary-color) !important;
        color: var(--primary-color) !important;
    }

    /* Metric styles */
    [data-testid="stMetricValue"] {
        color: var(--primary-color);
    }

    /* Removed aggressive explicit text overrides. Streamlit inherits var(--text-main) natively from .stApp injection. */
    /* Custom classes for the new workflow */
    .workflow-btn {
        background: none;
        border: none;
        padding: 0;
        cursor: pointer;
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# TOP NAVIGATION BAR (REDESIGNED)
# =========================
def show_top_navigation():
    page_icons = {
        "Upload & Overview": "📂",
        "AI Financial Management Report": "📈",
        "Cleaning & Preparation Studio": "🧹",
        "Visualization Builder": "📊",
        "Export & Report": "📤"
    }

    current_idx = PAGES.index(st.session_state.current_page)
    
    # Wrap everything in a relative container for the line to work
    st.markdown('<div style="position: relative; padding-bottom: 10px;">', unsafe_allow_html=True)
    st.markdown('<div class="stepper-line"></div>', unsafe_allow_html=True)
    
    cols = st.columns(len(PAGES))
    for i, page in enumerate(PAGES):
        status_class = ""
        icon = page_icons.get(page, "")
        
        if i < current_idx:
            status_class = "done"
            display_icon = "✓"
        elif i == current_idx:
            status_class = "active"
            display_icon = icon
        else:
            status_class = "pending"
            display_icon = icon
            
        with cols[i]:
            # Render the visual part
            html = f'<div class="stepper-item {status_class}">'
            html += f'<div class="step-counter {status_class}">{display_icon}</div>'
            html += f'<div class="step-name {status_class}">{page}</div>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
            
            # Navigation button below
            btn_label = "Active" if i == current_idx else ("Done" if i < current_idx else "Go")
            if st.button(btn_label, key=f"nav_btntop_{i}", use_container_width=True, type="primary" if i == current_idx else "secondary"):
                st.session_state.current_page = page
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True) # End relative container
    # st.divider() removed to reduce space


col_logo, col_dedication, col_undo, col_redo = st.columns([6, 6, 0.7, 0.7])
with col_logo:
    st.image("logo.png", width=450)
with col_dedication:
    st.markdown("""
    <div style="background-color: rgba(73, 136, 196, 0.1); 
                border: 1px solid rgba(73, 136, 196, 0.3); 
                border-radius: 10px; 
                padding: 15px; 
                margin-top: 10px;
                text-align: center;">
        <span style="color: #4988C4; font-weight: bold; font-size: 1.1rem; letter-spacing: 1px;">
            🎖️ Specially made for GDG Tashkent 19th April
        </span>
    </div>
    """, unsafe_allow_html=True)
with col_undo:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    if st.button("↩️", help="Undo last action", use_container_width=True):
        from logger import perform_undo
        perform_undo()
        st.rerun()
with col_redo:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    if st.button("↪️", help="Redo action", use_container_width=True):
        from logger import perform_redo
        perform_redo()
        st.rerun()

show_top_navigation()


# =========================
# SIDEBAR PANEL (TABS)
# =========================
st.sidebar.title("App Navigation")

if st.sidebar.button("🔄 Reset", use_container_width=True, help="Clear all data and start over"):
    st.session_state.clear()
    st.rerun()

render_toggle()

tab_filters, tab_logs = st.sidebar.tabs(["🗂️ Filters", "📝 History"])

with tab_filters:

    if "clean_df" in st.session_state and st.session_state["clean_df"] is not None:
        st.subheader("Live Preview")

        @st.dialog("Current Cleaned Dataset", width="large")
        def show_live_preview():
            df_to_show = st.session_state["clean_df"]
            st.caption(f"Showing current state: {df_to_show.shape[0]} rows, {df_to_show.shape[1]} columns")
            st.dataframe(df_to_show, use_container_width=True)

        if st.button("👀 Preview Cleaned Data", use_container_width=True, type="primary"):
            show_live_preview()
        st.markdown("---")

    if "transformation_logs" in st.session_state and st.session_state["transformation_logs"]:
        st.subheader("Applied Filters")
        logs = st.session_state["transformation_logs"]
        
        # Extract unique operations keeping first occurrence order
        applied_ops = []
        for log in logs:
            op_name = log.get("operation", "Unknown operation")
            # Map technical names to more user-friendly summaries if needed, or just use as is
            if op_name not in applied_ops:
                applied_ops.append(op_name)
        
        for i, op in enumerate(applied_ops, 1):
            st.markdown(f"**{i})** {op}")
    else:
        st.subheader("Applied Filters")
        st.write("No filters applied yet.")

with tab_logs:
    st.subheader("Transformation Logs")
    logs = st.session_state.get("transformation_logs", [])
    
    if not logs:
        st.info("No transformations recorded yet.")
    else:
        for reversed_idx, log in enumerate(reversed(logs)):
            actual_idx = len(logs) - 1 - reversed_idx
            col1, col2 = st.columns([5, 1])
            
            # Build a compact impact badge for the expander title
            ra = log.get("rows_affected") or {}
            impact_badge = ""
            if ra:
                if "rows_deleted" in ra:
                    impact_badge = f"  ·  🗑️ −{ra['rows_deleted']} rows"
                elif "cells_filled" in ra:
                    impact_badge = f"  ·  ✏️ {ra['cells_filled']} cells filled"
                elif "rows_modified" in ra:
                    impact_badge = f"  ·  ✏️ {ra['rows_modified']} rows changed"
                elif "rows_converted" in ra:
                    impact_badge = f"  ·  🔄 {ra['rows_converted']} converted"
                elif "columns_deleted" in ra:
                    impact_badge = f"  ·  🗑️ −{ra['columns_deleted']} cols"
                elif "columns_renamed" in ra:
                    impact_badge = f"  ·  ✏️ {ra['columns_renamed']} renamed"
                elif "columns_created" in ra:
                    impact_badge = f"  ·  ➕ {ra['columns_created']} col(s) added"
                elif "columns_converted" in ra:
                    impact_badge = f"  ·  🔄 {ra['columns_converted']} col(s)"
                elif "columns_scaled" in ra:
                    impact_badge = f"  ·  📐 {ra['columns_scaled']} col(s)"
                elif "values_capped" in ra:
                    impact_badge = f"  ·  ✂️ {ra['values_capped']} capped"
            
            with col1.expander(f"✨ Step {len(logs)-reversed_idx}: {log['operation']}{impact_badge}", expanded=False):
                st.caption(f"🕒 {log['timestamp']}")
                st.write(f"**Affected Columns:** {', '.join(log['columns'])}")
                # Show row impact
                if ra:
                    labels = {
                        "rows_deleted": "🗑️ Rows Deleted",
                        "cells_filled": "✏️ Cells Filled",
                        "rows_modified": "✏️ Rows Modified",
                        "rows_converted": "🔄 Values Converted",
                        "columns_deleted": "🗑️ Columns Deleted",
                        "columns_renamed": "✏️ Columns Renamed",
                        "columns_created": "➕ Columns Created",
                        "columns_converted": "🔄 Columns Converted",
                        "columns_scaled": "📐 Columns Scaled",
                        "values_capped": "✂️ Values Capped",
                        "bins": "🪣 Bins Created",
                    }
                    impact_lines = [f"- **{labels.get(k, k)}:** {v}" for k, v in ra.items()]
                    st.markdown("**📊 Impact:**\n" + "\n".join(impact_lines))
                # Show parameters
                params = log['parameters']
                if isinstance(params, dict):
                    param_lines = [f"- **{k}:** {v}" for k, v in params.items()]
                    st.markdown("**Parameters:**\n" + "\n".join(param_lines))
                else:
                    st.write(f"**Parameters:** {params}")
            
            if col2.button("✖", key=f"del_log_{actual_idx}", help="Undo this step (Warning: rolls back everything after it)"):
                from logger import checkpoint_state; checkpoint_state()
                if actual_idx == 0:
                    st.session_state["clean_df"] = st.session_state.get("df").copy(deep=True)
                    st.session_state["transformation_logs"] = []
                else:
                    prev_log = st.session_state["transformation_logs"][actual_idx - 1]
                    st.session_state["clean_df"] = prev_log.get("df_snapshot").copy(deep=True)
                    st.session_state["transformation_logs"] = st.session_state["transformation_logs"][:actual_idx]
                st.rerun()
                
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("⚠️ **Note:** Undoing a step will roll back your dataset to that exact point in time. Any steps performed after it will also be undone.")
        if st.button("🗑️ Clear All Logs", use_container_width=True):
            from logger import checkpoint_state; checkpoint_state()
            if "df" in st.session_state and st.session_state["df"] is not None:
                st.session_state["clean_df"] = st.session_state["df"].copy(deep=True)
            st.session_state["transformation_logs"] = []
            st.rerun()

# =========================
# MAIN LOGIC
# =========================
df = None
file_id = None

if "clean_df" not in st.session_state:
    st.session_state["clean_df"] = None

@st.dialog("Welcome to Call of Data!", width="large")
def show_upload_dialog():
    st.markdown("### Please provide a dataset to get started.")
    
    file_up = st.file_uploader("Upload dataset", type=["csv", "xlsx", "json"])
    st.markdown("---")
    st.markdown("**OR**")
    url_up = st.text_input("Paste Google Sheets link")
    btn_sheet = st.button("Read Sheet")
    
    if file_up:
        try:
            new_df = load_uploaded_file(file_up)
            st.session_state["df"] = new_df
            st.session_state["clean_df"] = new_df.copy()
            st.session_state["transformation_logs"] = []
            st.session_state["last_file_id"] = file_up.file_id
            st.session_state.current_page = "Upload & Overview"
            st.rerun()
        except Exception as e:
            st.error(f"⚠️ Could not load dataset. Please ensure it's a valid CSV/Excel/JSON file. (Error: {e})")
            
    elif btn_sheet:
        if url_up.strip():
            try:
                new_df = load_google_sheet(url_up.strip())
                st.session_state["df"] = new_df
                st.session_state["clean_df"] = new_df.copy()
                st.session_state["transformation_logs"] = []
                st.session_state["last_file_id"] = url_up.strip()
                st.session_state.current_page = "Upload & Overview"
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Could not load dataset from Google Sheets. Ensure the link is accessible. (Error: {e})")
        else:
            st.warning("Please paste a Google Sheets link first.")

if True:

    active_df = st.session_state.get("clean_df")
    if active_df is None:
        active_df = st.session_state.get("df", None)

    if active_df is None:
        show_upload_dialog()

    # =========================
    # PAGE RENDERING
    # =========================

    main_body = st.container()

    with main_body:
        if st.session_state.current_page == "Upload & Overview":
            st.header("Upload & Review Dataset")

            if active_df is not None:
                rows, cols = active_df.shape
                total_missing = int(active_df.isnull().sum().sum())
                total_duplicates = int(active_df.duplicated().sum())

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("# Rows", rows)
                m2.metric("# Columns", cols)
                m3.metric("Total Missing Values", total_missing)
                m4.metric("Duplicate Rows", total_duplicates)

                show_interactive_column_overview(active_df)
            else:
                st.info("Waiting for dataset upload...")

        elif st.session_state.current_page == "AI Financial Management Report":
            show_ai_financial_report(active_df)

        # -----------------------------------------------------

        elif st.session_state.current_page == "Cleaning & Preparation Studio":
            st.header("Cleaning & Preparation Studio")

            if active_df is not None:
                st.subheader("Select cleaning module")

                # Captain Price cleaning suggestion
                if st.button("🎖️ Ask Captain Price for Cleaning Suggestions", type="primary"):
                    with st.spinner("Captain Price is analyzing your dataset..."):
                        suggestions = get_cleaning_suggestions(active_df)
                    st.session_state["ai_cleaning_suggestions"] = suggestions
                
                if st.session_state.get("ai_cleaning_suggestions"):
                    with st.expander("🎖️ Captain Price’s Cleaning Plan", expanded=True):
                        st.markdown(st.session_state["ai_cleaning_suggestions"])
                        st.markdown("---")
                        st.markdown("**Do you want Captain Price to automatically apply these steps?**")
                        st.caption("⚠️ *This work is done by AI. Please check it for accuracy - might be mistakes.*")
                        c1, c2 = st.columns(2)
                        
                        if c1.button("✅ Apply Suggestions to Dataset", type="primary"):
                            with st.spinner("Captain Price is executing the native cleaning steps..."):
                                from ai_assistant import apply_native_actions
                                
                                try:
                                    updated_df = apply_native_actions(active_df, st.session_state["ai_cleaning_suggestions"])
                                    st.session_state["clean_df"] = updated_df
                                    st.success("Captain Price successfully applied all native changes!")
                                    del st.session_state["ai_cleaning_suggestions"]
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"⚠️ Captain Price's native actions failed. Error: {e}")
                        
                        if c2.button("Dismiss", key="dismiss_clean_sug"):
                            del st.session_state["ai_cleaning_suggestions"]
                            st.rerun()
                st.divider()

                cols = st.columns(4)
                modules = [
                    "Missing Values", "Duplicates", "Data Types", "Categorical Tools",
                    "Numeric Cleaning", "Normalization", "Column Operations", "Data Validation",
                    "Reshape & Transpose", "Anonymization"
                ]

                for i, module in enumerate(modules):
                    col = cols[i % 4]
                    selected_module = st.session_state.get("cleaning_module")
                    is_selected = (selected_module == module)
                    btn_type = "primary" if is_selected else "secondary"
                    if col.button(module, use_container_width=True, type=btn_type):
                        st.session_state["cleaning_module"] = module
                        st.session_state["cleaning_action"] = None
                        st.rerun()

                selected_module = st.session_state.get("cleaning_module")

                if selected_module == "Missing Values":
                    show_missing_values_cleaning(active_df)
                elif selected_module == "Duplicates":
                    show_duplicates_cleaning(active_df)
                elif selected_module == "Data Types":
                    show_data_types_cleaning(active_df)
                elif selected_module == "Categorical Tools":
                    show_categorical_tools(active_df)
                elif selected_module == "Numeric Cleaning":
                    show_numeric_cleaning(active_df)
                elif selected_module == "Normalization":
                    show_normalization_scaling(active_df)
                elif selected_module == "Column Operations":
                    show_column_operations(active_df)
                elif selected_module == "Data Validation":
                    show_data_validation(active_df)
                elif selected_module == "Reshape & Transpose":
                    show_reshape_tools(active_df)
                elif selected_module == "Anonymization":
                    show_anonymization_cleaning(active_df)
                elif selected_module:
                    st.info("Module coming next.")
            else:
                st.warning("Please upload dataset first.")

        # -----------------------------------------------------

        elif st.session_state.current_page == "Visualization Builder":
            show_visualization_builder(active_df)

        # -----------------------------------------------------

        elif st.session_state.current_page == "Export & Report":
            st.header("Export & Report")

            if active_df is not None:
                # 1. Dataset Export Section
                show_export_page(active_df)
                
            else:
                st.warning("Please upload and process a dataset first.")

    # =========================
    # CAPTAIN PRICE CHAT PANEL
    # =========================
    if active_df is not None:
        page = st.session_state.current_page
        ctx = build_dataset_context(active_df)
        if page == "Cleaning & Preparation Studio":
            ctx += "\n\n" + build_cleaning_context(active_df)
        elif page == "Visualization Builder":
            ctx += "\n\n" + build_viz_context(active_df)
        ctx += f"\n\nCurrent page: {page}"
        render_chat_panel(ctx)

# End of main block

# =========================
# FOOTER SECTION
# =========================
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
footer_cols = st.columns(3)

with footer_cols[0]:
    st.markdown("**Call of Data**")
    st.caption("Data Wrangling • Analysis • Insights")

with footer_cols[1]:
    st.markdown("**Built by Timur Nailev & Shohrukh Sunnatov**")
    st.caption("Westminster International University in Tashkent")

with footer_cols[2]:
    st.markdown("**Contact**")
    st.caption("Telegram: @shohrukhsunnatov, @Tim_Nilson")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 0.8rem; opacity: 0.6;'>© 2026 Call of Data • All rights reserved</p>", unsafe_allow_html=True)
