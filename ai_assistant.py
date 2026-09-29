"""
Captain Price — AI Assistant for Call of Data.
Uses Groq (free tier, Llama 3.3 70B) for context-aware data-science guidance.
"""

import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

env_key = os.getenv("GROQ_API_KEY", "")
try:
    secret_key = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    secret_key = ""

# st.write("ENV key found:", bool(env_key), "len:", len(env_key))
# st.write("SECRET key found:", bool(secret_key), "len:", len(secret_key))

# if env_key:
#     st.write("ENV prefix:", env_key[:8], "suffix:", env_key[-4:])
# if secret_key:
#     st.write("SECRET prefix:", secret_key[:8], "suffix:", secret_key[-4:])

GROQ_API_KEY = secret_key if secret_key else env_key
AI_READY = bool(GROQ_API_KEY)

MODEL_ID = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are **Captain Price**, the built-in AI assistant for "Call of Data" — a data-wrangling application.

Personality:
- You are direct, confident, knowledgeable, and slightly military-flavored (like the Call of Duty character).
- Use short, punchy sentences when possible.  Keep answers concise but complete.
- You may occasionally use phrases like "Roger that", "Copy", "Mission accomplished", etc., but don't overdo it.

Capabilities:
1. **Navigation help** — explain any feature of the app.
2. **Data-cleaning actions** — suggest specific moves using the app's **Native Actions**. You MUST return these as a JSON array of objects inside a ```json block.
    - **Supported Native Actions (JSON format):**
        - `{"op": "Convert to [Type]", "cols": [...]}` where [Type] is `Numeric`, `Datetime`, or `Categorical`. (Numeric uses a Smart Parser for currencies/K/M suffixes)
        - `{"op": "Drop rows with missing values", "cols": [...]}`
        - `{"op": "Drop Columns by Threshold", "cols": [...], "params": {"threshold": 50}}`
        - `{"op": "Fill Missing (Numeric)", "cols": [...], "params": {"method": "mean|median|constant", "fill_value": any}}`
        - `{"op": "Fill Missing (Categorical)", "cols": [...], "params": {"method": "mode|constant", "fill_value": any}}`
        - `{"op": "Remove Duplicates", "cols": [...], "params": {"keep": "first", "mode": "Full row|Subset"}}`
        - `{"op": "Drop Columns", "cols": [...]}`
        - `{"op": "Rename Columns", "cols": [], "params": {"renames": {"old": "new"}}}`
        - `{"op": "Create Column (Formula)", "cols": ["new_col"], "params": {"col_name": "new_col", "formula": "df['A'] + df['B']"}}`
        - `{"op": "Numeric Binning", "cols": ["new_col"], "params": {"strategy": "Equal Width", "bins": 5, "source_col": "A"}}`
        - `{"op": "Remove Outlier Rows", "cols": ["A"]}` (uses IQR)
        - `{"op": "Cap Outliers", "cols": ["A"], "params": {"lower": 10, "upper": 100}}`
        - `{"op": "Scale/Normalize", "cols": [...], "params": {"method": "Min-Max Scaling|Z-Score Standardization"}}`
        - `{"op": "Standardize Text", "cols": ["A"], "params": {"trim": true, "lower": false, "title": false}}`
        - `{"op": "Value Mapping", "cols": ["A"], "params": {"mapping": {"old": "new"}, "replace_unmatched": false}}`
        - `{"op": "One-Hot Encoding", "cols": ["A"]}`

    CRITICAL RULES:
    1. Only suggest actions if they actually improve the data.
    2. **Sequence is Vital**: Always suggest "Convert to Numeric" or "Standardize Text" BEFORE "Remove Outlier Rows" or "Scale/Normalize" if the columns are currently strings.
    3. Be careful with column names - use them exactly as they appear.
    4. Provide the rationale first, then a single JSON block at the end.
3. **Visualization recommendations** — suggest the best chart types and variable mappings for a dataset. You MUST only suggest from these 6 types: `Scatter Plot`, `Line Chart`, `Bar Chart`, `Histogram`, `Box Plot`, `Heatmap (Correlation)`.
    - For each suggestion, provide a structured JSON block wrapped in ```json that includes the title, explanation, chart_type, and a dictionary of `params` mapping to session state keys.
    - Keys to use in `params`:
        - Scatter Plot: `scat_x`, `scat_y`, `scat_c`. (Note: `scat_c_check` is handled by the app if `scat_c` is present).
        - Line Chart: `line_x`, `line_y`, `line_agg`, `line_time_agg`, `line_smooth` (int 1-100), `line_c`.
        - Bar Chart: `bar_x`, `bar_y`, `bar_agg`, `bar_top_n_slider` (int 1-100).
        - Histogram: `hist_x`, `hist_bins_slider` (int 5-100).
        - Box Plot: `box_y`, `box_x`.
        - Heatmap: `heat_vars` (list of column names).
4. **Chart analysis** — when given chart description / data summary, provide a brief analytical summary with key insights.

- Always answer in the context of the current dataset when one is loaded.
- If the user asks something unrelated to data or the app, briefly answer but steer back to the data task.
- Never fabricate column names. Only reference columns present in the provided context.
- **Action Execution**: When a user asks you to perform a specific data manipulation task (e.g., "drop column X", "fill missing in Y with 0"):
    - Identify the correct **Native Action(s)** from the list above.
    - Provide the action(s) in a ```json code block.
    - If it is IMPOSSIBLE or doesn't make sense (e.g., column doesn't exist), explicitly state "I cannot do that" and explain why. 
- Format cleaning suggestions as a numbered list.
- Keep chart analysis to 3-5 bullet points max.
- **Financial Report Template Design**: Suggest a structured report layout based on user goals and the dataset.
    - Output a JSON block wrapped in ```json with the following schema:
    ```json
    {
      "report_name": "Bank Financial Statement",
      "sections": [
        {
          "type": "summary_metrics",
          "title": "Account Summary",
          "kpis": ["col1", "col2"],
          "agg": "Sum|Average|Max|Min"
        },
        {
            "type": "details_table",
            "title": "Top Performance Transactions",
            "display_cols": ["Date", "Description", "Amount"],
            "sort_by": "Amount",
            "sort_order": "Descending",
            "limit": 20,
            "strategy": "Displaying Top 20 transactions by Value"
        },
        {
            "type": "ai_insights",
            "title": "Strategic Analytical Insights"
        },
        {
            "type": "trend_analysis",
            "title": "Financial Trend Observations"
        },
        {
          "type": "text_block",
          "title": "Corporate Disclaimer",
          "content": "This report is generated for internal management review purposes only."
        }
      ]
    }
    ```

    ```

9. **Canonical Mapping** — When given a list of categorical values and their frequencies, you suggest a "canonical" (standardized) name for each variant.
    - Group similar values (e.g., "M", "m", "Male" -> "Male").
    - You MUST return a JSON block wrapped in ```json using this EXACT schema:
    ```json
    {
      "mappings": [
        {"raw": "M", "canonical": "Male", "confidence": "High"},
        {"raw": "m", "canonical": "Male", "confidence": "High"},
        {"raw": "Female", "canonical": "Female", "confidence": "High"}
      ],
      "unmapped": ["Unknown", "N/A"]
    }
    ```
    - Confidence MUST be one of: `High`, `Medium`, `Low`.
    - Only suggest mappings you are certain about.
"""


def _get_client():
    """Return a Groq client or None if the API key isn't configured."""
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY)
    except Exception:
        return None


def build_dataset_context(df: pd.DataFrame, max_sample_rows: int = 5) -> str:
    """Build a compact text description of the current dataset for the LLM."""
    if df is None:
        return "No dataset is currently loaded."

    lines = []
    lines.append(f"Dataset shape: {df.shape[0]} rows × {df.shape[1]} columns")

    # Column info
    col_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        missing = int(df[col].isna().sum())
        unique = int(df[col].nunique())
        col_info.append(f"  - {col} (type={dtype}, missing={missing}, unique={unique})")
    lines.append("Columns:\n" + "\n".join(col_info))

    # Quick stats for numeric columns
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if num_cols:
        desc = df[num_cols].describe().round(2).to_string()
        lines.append(f"Numeric summary:\n{desc}")

    # Sample rows
    sample = df.head(max_sample_rows).to_string(max_colwidth=40)
    lines.append(f"Sample rows:\n{sample}")

    return "\n\n".join(lines)


def build_cleaning_context(df: pd.DataFrame) -> str:
    """Extra cleaning-specific context."""
    if df is None:
        return ""
    lines = []
    total_missing = int(df.isna().sum().sum())
    total_dups = int(df.duplicated().sum())
    lines.append(f"Total missing cells: {total_missing}")
    lines.append(f"Duplicate rows: {total_dups}")

    # Columns with >20 % missing
    pct = df.isna().mean()
    high_missing = pct[pct > 0.2]
    if not high_missing.empty:
        items = [f"{c} ({v:.0%})" for c, v in high_missing.items()]
        lines.append(f"Columns with >20% missing: {', '.join(items)}")

    return "\n".join(lines)


def build_viz_context(df: pd.DataFrame) -> str:
    """Extra visualization-specific context."""
    if df is None:
        return ""
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    dt_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    lines = [
        f"Numeric columns ({len(num_cols)}): {', '.join(num_cols[:15])}",
        f"Categorical columns ({len(cat_cols)}): {', '.join(cat_cols[:15])}",
        f"Datetime columns ({len(dt_cols)}): {', '.join(dt_cols[:10])}",
    ]
    return "\n".join(lines)


def call_captain_price(user_message: str, context: str, history: list | None = None) -> str:
    """Send a message to Captain Price and get a response.

    Args:
        user_message: The user's question / request.
        context: A text block describing the current dataset and page.
        history: Optional list of prior {"role": ..., "content": ...} dicts.

    Returns:
        The assistant's reply text, or an error message.
    """
    client = _get_client()
    if client is None:
        return ("⚠️ **Captain Price is offline.** "
                "Please set your `GROQ_API_KEY` in the `.env` file at the project root to enable AI features. "
                "Get a free key at https://console.groq.com")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        messages.append({"role": "system", "content": f"Current dataset context:\n{context}"})

    if history:
        messages.extend(history[-10:])  # keep last 10 exchanges to save tokens

    messages.append({"role": "user", "content": user_message})

    try:
        resp = client.chat.completions.create(
            model=MODEL_ID,
            messages=messages,
            temperature=0.4,
            max_tokens=1200,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠️ Captain Price encountered an error: {e}"


# ---------------------------------------------------------------------------
# Streamlit UI helpers
# ---------------------------------------------------------------------------

def inject_toggle_css():
    """Inject the floating toggle button CSS (bottom-right corner)."""
    st.markdown("""
    <style>
        .captain-float {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999999;
            background: rgba(30,30,30,0.9);
            padding: 10px;
            border: 1px solid #22c55e;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
    </style>
    """, unsafe_allow_html=True)


def render_toggle():
    """Render the Captain Price ON/OFF toggle in a floating container."""
    if "ai_enabled" not in st.session_state:
        st.session_state["ai_enabled"] = False
    
    inject_toggle_css()
    
    # Render outside of sidebar to be truly floating via CSS
    with st.container():
        st.markdown('<div class="captain-float">', unsafe_allow_html=True)
        st.session_state["ai_enabled"] = st.toggle(
            "🎖️ Captain Price AI",
            value=st.session_state["ai_enabled"],
            key="captain_ai_toggle",
            help="Enable or disable AI assistant globally"
        )
        if st.session_state["ai_enabled"]:
            st.markdown('<small style="color:#22c55e">Online</small>', unsafe_allow_html=True)
        else:
            st.markdown('<small style="color:#ef4444">Offline</small>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_chat_panel(page_context: str):
    """Render the chat panel at the bottom of the current page when AI is enabled."""
    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = []

    if not st.session_state.get("ai_enabled", False):
        return

    st.markdown("---")
def apply_native_actions(df: pd.DataFrame, actions_json: str) -> pd.DataFrame:
    """Execute a list of Native Actions on the dataframe and log them correctly."""
    import json
    import re
    from logger import checkpoint_state, add_log
    import numpy as np
    
    # Extract JSON
    json_match = re.search(r"```json\n(.*?)\n```", actions_json, re.DOTALL)
    if not json_match:
        try:
            actions = json.loads(actions_json)
        except:
            raise ValueError("No valid JSON actions found.")
    else:
        actions = json.loads(json_match.group(1))

    working_df = df.copy()
    
    for action in actions:
        op = action.get("op", "")
        cols = action.get("cols", [])
        p = action.get("params", {})
        
        checkpoint_state() # Backup before each step
        
        # --- IMPLEMENTATION LOGIC (Mirrors manual UI) ---
        
        # 1. DATA TYPES
        if op == "Convert to Numeric":
            from utils import smart_parse_numeric
            for c in cols:
                working_df[c] = working_df[c].apply(smart_parse_numeric)
            add_log(op, {"action": "smart_parse"}, cols, rows_affected={"columns_converted": len(cols)})

        elif op == "Convert to Datetime":
            fmt = p.get("format")
            for c in cols:
                working_df[c] = pd.to_datetime(working_df[c], format=fmt, errors="coerce")
            add_log(op, {"format": fmt or "Auto-detected"}, cols, rows_affected={"rows_converted": len(working_df)})

        elif op == "Convert to Categorical":
            for c in cols:
                working_df[c] = working_df[c].astype("category")
            add_log(op, {"action": "to_category"}, cols, rows_affected={"columns_converted": len(cols)})

        # 2. MISSING VALUES
        elif op == "Drop rows with missing values":
            before = len(working_df)
            working_df = working_df.dropna(subset=cols)
            add_log(op, "Rows containing Nulls were permanently removed", cols, rows_affected={"rows_deleted": before - len(working_df)})

        elif op == "Drop Columns by Threshold":
            threshold = p.get("threshold", 50)
            missing_pct = working_df.isnull().mean() * 100
            cols_to_drop = missing_pct[missing_pct > threshold].index.tolist()
            working_df = working_df.drop(columns=cols_to_drop)
            add_log(op, f"Threshold > {threshold}%", cols_to_drop, rows_affected={"columns_deleted": len(cols_to_drop)})

        elif "Fill Missing" in op:
            method = p.get("method", "mean").lower()
            fill_val = p.get("fill_value")
            is_numeric = "Numeric" in op
            for c in cols:
                series = working_df[c]
                filled_count = int(series.isna().sum())
                if method == "mean": working_df[c] = series.fillna(series.mean())
                elif method == "median": working_df[c] = series.fillna(series.median())
                elif method == "mode": working_df[c] = series.fillna(series.mode()[0])
                elif method == "forward fill": working_df[c] = series.fillna(method="ffill")
                elif method == "backward fill": working_df[c] = series.fillna(method="bfill")
                elif method == "constant": working_df[c] = series.fillna(fill_val)
                add_log(op, {"method": method, "fill_value": fill_val}, [c], rows_affected={"cells_filled": filled_count})

        # 3. DUPLICATES
        elif op.startswith("Remove Duplicates"):
            keep = p.get("keep", "first")
            mode = p.get("mode", "Full row")
            subset = cols if mode == "Subset" else None
            before = len(working_df)
            working_df = working_df.drop_duplicates(subset=subset, keep=keep)
            add_log(op, {"keep": keep, "mode": mode}, cols if subset else list(working_df.columns), rows_affected={"rows_deleted": before - len(working_df)})

        # 4. COLUMNS
        elif op == "Drop Columns":
            working_df = working_df.drop(columns=cols, errors="ignore")
            add_log(op, "Permanently removed entirely from dataset", cols, rows_affected={"columns_deleted": len(cols)})

        elif op == "Rename Columns":
            renames = p.get("renames", {})
            working_df = working_df.rename(columns=renames)
            add_log(op, {"renames": renames}, list(renames.values()), rows_affected={"columns_renamed": len(renames)})

        elif op == "Create Column (Formula)":
            col_name = p.get("col_name", "new_col")
            formula = p.get("formula", "")
            # Basic sanitization and evaluation (mimics clean_columns.py)
            allowed_names = {"log": np.log, "sqrt": np.sqrt, "abs": np.abs, "if": np.where, "np": np}
            working_df[col_name] = eval(formula.replace("df", "working_df"), {"__builtins__": None, "working_df": working_df}, allowed_names)
            add_log(op, {"col_name": col_name, "formula": formula}, [col_name], rows_affected={"columns_created": 1})

        # 5. NUMERIC / OUTLIERS
        elif op == "Remove Outlier Rows":
            from utils import smart_parse_numeric
            for c in cols:
                # Ensure numeric type before IQR
                s = working_df[c]
                if not pd.api.types.is_numeric_dtype(s):
                    s = s.apply(smart_parse_numeric)
                
                s_clean = s.dropna()
                if s_clean.empty: continue
                
                q1, q3 = s_clean.quantile(0.25), s_clean.quantile(0.75)
                iqr = q3 - q1
                before = len(working_df)
                # Apply filter to the main df using the converted series
                working_df = working_df[~((s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr))]
                add_log(op, f"Removed {before - len(working_df)} rows", [c], rows_affected={"rows_deleted": before - len(working_df)})

        elif op == "Cap Outliers":
            from utils import smart_parse_numeric
            l, u = p.get("lower"), p.get("upper")
            for c in cols:
                if not pd.api.types.is_numeric_dtype(working_df[c]):
                    working_df[c] = working_df[c].apply(smart_parse_numeric)
                
                before_vals = working_df[c].copy()
                working_df[c] = working_df[c].clip(lower=l, upper=u)
                changed = int((before_vals != working_df[c]).sum())
                add_log(op, {"lower": l, "upper": u}, [c], rows_affected={"values_capped": changed})

        elif op.startswith("Scale/Normalize"):
            from utils import smart_parse_numeric
            method = p.get("method", "Min-Max Scaling")
            for c in cols:
                if not pd.api.types.is_numeric_dtype(working_df[c]):
                    working_df[c] = working_df[c].apply(smart_parse_numeric)
                
                s = working_df[c]
                if "Min-Max" in method: working_df[c] = (s - s.min()) / (s.max() - s.min())
                else: working_df[c] = (s - s.mean()) / s.std()
            add_log(op, {"method": method}, cols, rows_affected={"columns_scaled": len(cols)})

        # 6. CATEGORICAL
        elif op == "Standardize Text":
            trim, low, titl = p.get("trim"), p.get("lower"), p.get("title")
            for c in cols:
                res = working_df[c].astype(str)
                if trim: res = res.str.strip()
                if low: res = res.str.lower()
                if titl: res = res.str.title()
                working_df[c] = res
            add_log(op, {"trim": trim, "lower": low, "title": titl}, cols, rows_affected={"rows_modified": len(working_df)})

        elif op == "Value Mapping":
            mapping = p.get("mapping", {})
            rep_other = p.get("replace_unmatched", False)
            for c in cols:
                working_df[c] = working_df[c].replace(mapping)
                if rep_other:
                    mapped = set(mapping.values())
                    working_df[c] = working_df[c].apply(lambda x: x if pd.isna(x) or x in mapped else "Other")
            add_log(op, {"mapping": mapping, "replace_unmatched": rep_other}, cols, rows_affected={"rows_modified": len(working_df)})

        elif op == "One-Hot Encoding":
            for c in cols:
                dummies = pd.get_dummies(working_df[c], prefix=c).astype(int)
                working_df = pd.concat([working_df.drop(columns=[c]), dummies], axis=1)
                add_log(op, {"num_columns": len(dummies.columns)}, [c], rows_affected={"columns_created": len(dummies.columns)})

        elif op == "Numeric Binning":
            strategy = p.get("strategy", "Equal Width")
            bins = p.get("bins", 5)
            source_col = p.get("source_col")
            new_col = cols[0] if cols else f"{source_col}_Binned"
            if strategy == "Equal Width":
                working_df[new_col] = pd.cut(working_df[source_col], bins=bins).astype(str)
            else:
                working_df[new_col] = pd.qcut(working_df[source_col], q=bins, duplicates='drop').astype(str)
            add_log(op, {"strategy": strategy, "bins": bins, "source_col": source_col}, [new_col], rows_affected={"columns_created": 1})

        elif op == "Rare Grouping":
            rare_cats = p.get("rare_categories", [])
            for c in cols:
                working_df[c] = working_df[c].apply(lambda x: "Other" if x in rare_cats else x)
            add_log(op, {"rare_categories": rare_cats}, cols, rows_affected={"rows_modified": len(working_df)})

    return working_df


def _render_assistant_message(content: str, index: int):
    """Internal helper to render an assistant message with optional execution logic."""
    with st.chat_message("assistant", avatar="🎖️"):
        st.write(content)

        import re
        import json
        # Improved regex to catch ```json code block
        json_match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
        
        if json_match:
            st.info("🎖️ **Captain Price can execute these tactical maneuvers for you.**")
            st.caption("⚠️ *This work is done by AI using the app's native tools.*")
            
            exec_btn_key = f"exec_chat_msg_{index}"
            if "ai_executed_indices" not in st.session_state:
                st.session_state["ai_executed_indices"] = set()

            is_done = index in st.session_state["ai_executed_indices"]
            btn_label = "✅ EXECUTED" if is_done else "✅ Execute Native Actions"
            
            if st.button(btn_label, key=exec_btn_key, disabled=is_done, type="primary" if not is_done else "secondary"):
                if "clean_df" not in st.session_state:
                    st.error("No active dataset to modify.")
                    return

                try:
                    # USE THE NEW NATIVE DRIVER
                    updated_df = apply_native_actions(st.session_state["clean_df"], content)
                    
                    st.session_state["clean_df"] = updated_df
                    st.session_state["ai_executed_indices"].add(index)
                    st.success("Mission accomplished. All actions logged and reproducible.")
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Operation failed: {e}")


def render_chat_panel(page_context: str):
    """Render the chat panel at the bottom of the current page when AI is enabled."""
    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = []

    if not st.session_state.get("ai_enabled", False):
        return

    st.markdown("---")
    st.markdown("### 🎖️ Captain Price — Tactical Assistance")
    
    with st.container(border=True):
        # Display message history
        for i, msg in enumerate(st.session_state.get("ai_messages", [])):
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                _render_assistant_message(msg["content"], i)

    # Chat input
    user_input = st.chat_input("Ask Captain Price anything...", key="captain_chat_input")
    if user_input:
        st.session_state["ai_messages"].append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        with st.spinner("Captain Price is thinking..."):
            reply = call_captain_price(
                user_input,
                context=page_context,
                history=st.session_state["ai_messages"][:-1],
            )
        
        # Append immediately to avoid missing it on rerun
        st.session_state["ai_messages"].append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state["ai_messages"]:
        if st.button("Clear Chat History", key="clear_ai_chat"):
            st.session_state["ai_messages"] = []
            st.rerun()


def get_cleaning_suggestions(df: pd.DataFrame) -> str:
    """Ask Captain Price for cleaning suggestions as structured Native Actions."""
    ctx = build_dataset_context(df) + "\n\n" + build_cleaning_context(df)
    prompt = ("Analyze this dataset and suggest the top 3-5 standard cleaning actions needed. "
              "You MUST only use the 'Native Actions' defined in your system prompt. "
              "Provide a brief written justification for each step, and then provide "
              "the final set of actions as a combined JSON array inside a ```json block. "
              "This allows me to execute them natively.")
    return call_captain_price(prompt, context=ctx)




def get_viz_suggestions(df: pd.DataFrame) -> str:
    """Ask Captain Price for visualization recommendations in structured JSON format."""
    ctx = build_dataset_context(df) + "\n\n" + build_viz_context(df)
    prompt = ("Suggest the 3-5 most useful charts for this dataset using ONLY the 6 allowed chart types. "
              "For each chart, provide a title, a brief explanation, the chart_type, and the 'params' dictionary "
              "with the specific session state keys I gave you in your system prompt. "
              "Output the results as a JSON array inside a ```json code block.")
    return call_captain_price(prompt, context=ctx)


def get_chart_analysis(df: pd.DataFrame, chart_type: str, x_col: str, y_col: str = None, color_col: str = None) -> str:
    """Ask Captain Price to analyze a rendered chart."""
    ctx = build_dataset_context(df)
    desc_parts = [f"Chart type: {chart_type}", f"X-axis: {x_col}"]
    if y_col:
        desc_parts.append(f"Y-axis: {y_col}")
    if color_col:
        desc_parts.append(f"Color grouping: {color_col}")

    # Add summary stats for relevant columns
    cols_used = [c for c in [x_col, y_col, color_col] if c and c in df.columns and c != "(Count Rows)"]
    if cols_used:
        stats = df[cols_used].describe().round(2).to_string()
        desc_parts.append(f"\nStats for plotted columns:\n{stats}")

    chart_desc = "\n".join(desc_parts)
    prompt = (f"I just created this chart:\n{chart_desc}\n\n"
              "Give a brief analytical summary (3-5 bullet points) of what insights "
              "this chart likely reveals. Focus on trends, outliers, distributions, "
              "or notable patterns.")
    return call_captain_price(prompt, context=ctx)


def get_story_contract_interpretation(df: pd.DataFrame, inputs: dict) -> str:
    """Ask Captain Price to interpret a Story Contract and return structured JSON."""
    ctx = build_dataset_context(df) + "\n\n" + build_viz_context(df)
    
    input_str = "\n".join([f"- {k}: {v}" for k, v in inputs.items() if v])
    
    prompt = (
        "Interpret the following Story Contract and recommend the best visualization strategy.\n"
        f"USER INPUTS:\n{input_str}\n\n"
        "Analyze the inputs against the available columns. "
        "Recommend the most effective chart type, axes, and settings. "
        "You MUST return the interpretation as a single JSON object inside a ```json block "
        "following the schema defined in your instructions. "
        "Be specific with column names and aggregation choices."
    )
    return call_captain_price(prompt, context=ctx)


def get_canonical_mapping(column_name: str, value_counts: dict) -> str:
    """Ask Captain Price to suggest a canonical mapping for categorical values."""
    # Convert dict to sorted string for context
    items = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
    val_str = "\n".join([f"- {val}: {count} occurrences" for val, count in items[:100]])
    
    prompt = (
        f"Analyze the categorical column '{column_name}' and suggest a canonical mapping to standardize the values.\n"
        f"UNIQUE VALUES & FREQUENCIES:\n{val_str}\n\n"
        "Go through these values and identify different variants of the same concept (e.g., abbreviations, typos, casing differences). "
        "Recommend a single 'canonical' name for each group. "
        "You MUST return the results as a single JSON object inside a ```json block "
        "following the schema defined in your instructions. "
        "Be conservative with 'High' confidence; only use it for obvious matches."
    )
def get_report_template_suggestion(df: pd.DataFrame, user_request: str) -> str:
    """Ask Captain Price to design a report template based on user guidance."""
    ctx = build_dataset_context(df) + "\n\n" + build_viz_context(df)
    prompt = (
        f"Design a professional financial report template based on this request: '{user_request}'.\n"
        "Analyze the dataset columns and map them to the sections of the report. "
        "Try to follow a professional 'Bank Statement' style if appropriate. "
        "Include placeholders for strategic sections like 'AI Insights' or 'Trend Analysis'. "
        "IMPORTANT: Only use numeric columns for 'kpis' in summary_metrics. "
        "Return the justification followed by the JSON configuration block."
    )
    return call_captain_price(prompt, context=ctx)

def get_financial_insights(df: pd.DataFrame, report_context: str) -> str:
    """Ask Captain Price for deep financial insights and recommendations."""
    ctx = build_dataset_context(df, max_sample_rows=10)
    prompt = (
        "Act as a Senior Financial Analyst. Analyze this report context and dataset to provide executive insights. "
        "Strictly return ONLY the sections requested below. Do NOT include phrases like 'Step X', 'Final Answer', "
        "or any introductory/concluding metadata. Return clean, professional text with markdown bolding for headers.\n\n"
        f"CONTEXT: {report_context}\n\n"
        "REQUIRED FORMAT:\n"
        "**Strategic Performance Insights**\n(Professional analysis here)\n\n"
        "**Tactical Strategic Recommendations**\n(Concrete actions here)\n\n"
        "**Recommended Visualizations**\n"
        "```json\n"
        "[{\"title\": \"Chart Title\", \"chart_type\": \"Bar|Line\", \"x_col\": \"column_x\", \"y_col\": \"column_y\"}]\n"
        "```\n"
        "CRITICAL: Ensure 'y_col' is always a numeric column."
    )
    return call_captain_price(prompt, context=ctx)
