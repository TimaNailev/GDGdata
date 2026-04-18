import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


def is_identifier_like(series: pd.Series, col_name: str) -> bool:
    s = series.dropna()
    if s.empty:
        return False
    col_name_lower = str(col_name).strip().lower()
    id_keywords = ["id", "code", "uuid", "key", "identifier"]
    if any(keyword in col_name_lower for keyword in id_keywords):
        return True
    unique_ratio = s.nunique() / len(s)
    if unique_ratio >= 0.95:
        return True
    return False


def detect_column_kind(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    converted = pd.to_datetime(series, errors="coerce")
    non_null_original = series.notna().sum()
    if non_null_original > 0:
        valid_ratio = converted.notna().sum() / non_null_original
        if valid_ratio >= 0.7:
            return "datetime"
    return "categorical"


def show_numeric_details(series: pd.Series, col_name: str):
    clean = series.dropna()
    st.subheader(f"Further Information: {col_name}")
    if clean.empty:
        st.warning("This column contains only missing values.")
        return

    mode_vals = clean.mode()
    mode_val = mode_vals.iloc[0] if not mode_vals.empty else "No mode"

    stats_df = pd.DataFrame({
        "Statistic": [
            "Count (non-missing)", "Missing values", "Missing %",
            "Mean", "Median", "Mode", "Min", "Max", "Std", "Unique values"
        ],
        "Value": [
            int(clean.count()), int(series.isna().sum()),
            round(series.isna().mean() * 100, 2),
            round(clean.mean(), 4), round(clean.median(), 4), mode_val,
            round(clean.min(), 4), round(clean.max(), 4),
            round(clean.std(), 4) if clean.count() > 1 else 0,
            int(clean.nunique())
        ]
    })
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

    if is_identifier_like(series, col_name):
        st.info("This column looks like an identifier, so no distribution chart is shown.")
        return

    st.markdown("**Distribution**")
    fig, ax = plt.subplots()
    ax.hist(clean.astype(float), bins=12)
    ax.set_xlabel(col_name)
    ax.set_ylabel("Count")
    st.pyplot(fig, clear_figure=True)


def show_datetime_details(series: pd.Series, col_name: str):
    converted = pd.to_datetime(series, errors="coerce")
    clean = converted.dropna()
    st.subheader(f"Further Information: {col_name}")
    if clean.empty:
        st.warning("This column could not be interpreted as valid datetime values.")
        return

    stats_df = pd.DataFrame({
        "Statistic": [
            "Count (valid datetime)", "Missing / invalid values",
            "Missing / invalid %", "Earliest date", "Latest date", "Unique timestamps"
        ],
        "Value": [
            int(clean.count()), int(converted.isna().sum()),
            round(converted.isna().mean() * 100, 2),
            str(clean.min()), str(clean.max()), int(clean.nunique())
        ]
    })
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

    view_mode = st.radio(
        f"View time pattern for {col_name}",
        ["Monthly", "Daily"], horizontal=True,
        key=f"datetime_view_{col_name}"
    )

    if view_mode == "Monthly":
        month_order = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        month_counts = clean.dt.month_name().value_counts()
        month_counts = month_counts.reindex(month_order, fill_value=0)
        fig, ax = plt.subplots()
        ax.bar(month_counts.index, month_counts.values)
        ax.set_xlabel("Month")
        ax.set_ylabel("Count")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig, clear_figure=True)
    else:
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_counts = clean.dt.day_name().value_counts()
        weekday_counts = weekday_counts.reindex(weekday_order, fill_value=0)
        fig, ax = plt.subplots()
        ax.bar(weekday_counts.index, weekday_counts.values)
        ax.set_xlabel("Weekday")
        ax.set_ylabel("Count")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig, clear_figure=True)


def show_categorical_details(series: pd.Series, col_name: str):
    clean = series.dropna().astype(str)
    st.subheader(f"Further Information: {col_name}")
    if clean.empty:
        st.warning("This column contains only missing values.")
        return

    mode_vals = clean.mode()
    mode_val = mode_vals.iloc[0] if not mode_vals.empty else "No mode"
    value_counts = clean.value_counts(dropna=False)
    top_10 = value_counts.head(10)

    stats_df = pd.DataFrame({
        "Statistic": [
            "Count (non-missing)", "Missing values", "Missing %",
            "Unique categories", "Most frequent category (mode)", "Mode frequency"
        ],
        "Value": [
            int(clean.count()), int(series.isna().sum()),
            round(series.isna().mean() * 100, 2),
            int(clean.nunique()), mode_val,
            int(top_10.iloc[0]) if len(top_10) > 0 else 0
        ]
    })
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

    st.markdown("**Top categories**")
    top_cat_df = pd.DataFrame({
        "Category": top_10.index.astype(str),
        "Count": top_10.values,
        "Percent %": ((top_10.values / len(clean)) * 100).round(2)
    })
    st.dataframe(top_cat_df, use_container_width=True, hide_index=True)

    if is_identifier_like(series, col_name):
        st.info("This column looks like an identifier, so no chart is shown.")
        return

    st.markdown("**Category frequency chart**")
    fig, ax = plt.subplots()
    ax.bar(top_10.index.astype(str), top_10.values)
    ax.set_xlabel(col_name)
    ax.set_ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig, clear_figure=True)


def make_dtype_readable(series: pd.Series) -> str:
    detected = detect_column_kind(series)
    if detected == "datetime":
        return "Datetime"
    if detected == "numeric":
        return "Number"
    unique_ratio = series.dropna().nunique() / max(len(series.dropna()), 1)
    if unique_ratio < 0.5:
        return "Categorical"
    return "Text"


def get_column_diagnostics(series: pd.Series, col_name: str) -> dict:
    """Analyzes a single column for quality issues and returns a diagnostic dict."""
    issues = []
    severity = "Low"
    action = "None"
    
    total = len(series)
    null_count = int(series.isna().sum())
    null_pct = (null_count / total) * 100 if total > 0 else 0
    unique_count = int(series.dropna().nunique())
    
    # 1. Missing Values
    if null_count > 0:
        if null_pct > 30:
            issues.append(f"High missing data ({null_pct:.1f}%)")
            severity = "High"
            action = "Missing Value Cleaner (Drop/Impute)"
        elif null_pct > 10:
            issues.append(f"Significant missing data ({null_pct:.1f}%)")
            severity = "Medium" if severity != "High" else "High"
            action = "Missing Value Cleaner"
        else:
            issues.append("Minor missing values")
            action = "Missing Value Cleaner"

    # 2. Placeholders (N/A, ?, etc.)
    placeholders = ["?", "N/A", "NA", "null", "-", "none"]
    s_str = series.dropna().astype(str).str.strip().str.lower()
    found_placeholders = [p for p in placeholders if p in s_str.values]
    if found_placeholders:
        issues.append(f"Placeholder values found: {', '.join(found_placeholders)}")
        severity = "Medium" if severity == "Low" else severity
        action = "Missing Value Cleaner / Replace"

    # 3. Numeric-as-Text
    if detect_column_kind(series) == "categorical":
        # Check if >90% of non-nulls can be numeric
        numeric_conversion = pd.to_numeric(series.dropna(), errors='coerce')
        valid_num_ratio = numeric_conversion.notna().sum() / max(len(series.dropna()), 1)
        if valid_num_ratio > 0.9:
            issues.append("Numeric data stored as Text")
            severity = "High"
            action = "Data Type Cleaner"

    # 4. Inconsistent Categorical (Casing/Whitespace)
    if detect_column_kind(series) == "categorical":
        raw_uniques = set(series.dropna().astype(str))
        clean_uniques = set(series.dropna().astype(str).str.strip().str.lower())
        if len(clean_uniques) < len(raw_uniques):
            issues.append("Inconsistent casing or extra spaces")
            action = "Categorical Tools (Clean Labels)"
            if severity == "Low": severity = "Medium"

    # 5. Leading/Trailing Whitespace
    if series.dtype == 'object':
        s_clean = series.dropna().astype(str)
        has_whitespace = (s_clean.str.strip() != s_clean).any()
        if has_whitespace:
            issues.append("Leading/trailing whitespace detected")
            action = "Categorical Tools / Column Ops"

    # 6. Constant Columns
    if unique_count == 1:
        issues.append("Constant value column (Zero variance)")
        severity = "Medium"
        action = "Column Operations (Drop)"

    # 7. High Cardinality
    if detect_column_kind(series) == "categorical" and unique_count > 50 and not is_identifier_like(series, col_name):
        issues.append(f"High cardinality ({unique_count} categories)")
        action = "Categorical Tools (Group/Bin)"

    # 8. Duplicate IDs
    if is_identifier_like(series, col_name) and not series.is_unique:
        issues.append("Duplicate identifiers found in ID-like column")
        severity = "High"
        action = "Duplicate / Validation Cleaner"

    # Escalate if multiple issues
    if len(issues) > 2 and severity != "High":
        severity = "Medium"
    
    return {
        "Column": col_name,
        "Type": make_dtype_readable(series),
        "Nulls": f"{null_count} ({null_pct:.1f}%)",
        "Uniques": unique_count,
        "Issues": " | ".join(issues) if issues else "✨ Clean",
        "Severity": severity if issues else "N/A",
        "Action": action
    }


@st.cache_data
def get_column_overview_df(df: pd.DataFrame) -> pd.DataFrame:
    total_rows = len(df)
    overview_df = pd.DataFrame({
        "Further Information": [False] * len(df.columns),
        "Column Name": df.columns,
        "Data Type": [make_dtype_readable(df[col]) for col in df.columns],
        "Missing Values": df.isnull().sum().values,
    })
    overview_df["Missing %"] = (
        (overview_df["Missing Values"] / total_rows) * 100
    ).round(2)
    return overview_df


def show_interactive_column_overview(df: pd.DataFrame):
    st.markdown("### Column Overview")
    
    # QUALITY REPORT TOGGLE
    if "show_quality_report" not in st.session_state:
        st.session_state.show_quality_report = False

    c1, c2 = st.columns([2, 5])
    if c1.button("🔍 Run Quality Report", type="primary", use_container_width=True):
        st.session_state.show_quality_report = not st.session_state.show_quality_report

    if st.session_state.show_quality_report:
        render_quality_report(df)

    overview_df = get_column_overview_df(df)

    edited_df = st.data_editor(
        overview_df, use_container_width=True, hide_index=True,
        disabled=["Column Name", "Data Type", "Missing Values", "Missing %"],
        column_config={
            "Further Information": st.column_config.CheckboxColumn(
                "Further Information",
                help="Tick to show detailed information for this column"
            )
        },
        key="column_overview_editor"
    )

    selected_rows = edited_df[edited_df["Further Information"] == True]
    if len(selected_rows) == 0:
        return

    st.markdown("---")
    st.markdown("## Detailed Column Information")

    for _, row in selected_rows.iterrows():
        selected_col = row["Column Name"]
        selected_series = df[selected_col]
        detected_kind = detect_column_kind(selected_series)

        with st.container(border=True):
            if detected_kind == "numeric":
                show_numeric_details(selected_series, selected_col)
            elif detected_kind == "datetime":
                show_datetime_details(selected_series, selected_col)
            else:
                show_categorical_details(selected_series, selected_col)
            st.markdown("")


def render_quality_report(df: pd.DataFrame):
    """Generates and displays the diagnostic quality report."""
    st.markdown("---")
    st.markdown("### 📋 Dataset Quality Diagnostic")
    
    # 1. Overall Summary Metrics
    total_slots = df.size
    total_missing = int(df.isna().sum().sum())
    dup_rows = int(df.duplicated().sum())
    
    # Diagnostic Collection
    diag_data = []
    for col in df.columns:
        diag_data.append(get_column_diagnostics(df[col], col))
    
    diag_df = pd.DataFrame(diag_data)
    cols_with_issues = len(diag_df[diag_df["Issues"] != "✨ Clean"])
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Rows", f"{len(df):,}")
    m2.metric("Total Cols", f"{len(df.columns)}")
    m3.metric("Missing Cells", f"{total_missing:,}")
    m4.metric("Duplicate Rows", f"{dup_rows:,}")
    m5.metric("Cols w/ Issues", f"{cols_with_issues}")

    # 2. Detailed Diagnostic Table
    st.markdown("**Column-Level Diagnostics**")
    
    def color_severity(val):
        color = '#64748b' # Default gray
        if val == 'High': color = '#ef4444' # Tailwind Red 500
        elif val == 'Medium': color = '#f59e0b' # Tailwind Amber 500
        elif val == 'Low': color = '#4988C4' # Professional Primary Blue
        return f'color: {color}; font-weight: bold'

    if not diag_df.empty:
        # Display table with formatting pointers
        st.dataframe(
            diag_df.style.map(color_severity, subset=['Severity']),
            use_container_width=True,
            hide_index=True
        )
    
    st.caption("💡 *Severity is calculated based on missing density, duplicate ID risks, and structural formatting consistency.*")
    st.markdown("---")
