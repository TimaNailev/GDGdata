import re
import numpy as np
import pandas as pd
import streamlit as st
from logger import add_log, checkpoint_state


def show_column_operations(df: pd.DataFrame):
    st.subheader("Column Operations")

    if st.session_state.get("clean_df") is None:
        st.session_state["clean_df"] = df.copy()

    working_df = st.session_state["clean_df"]

    # Action Selection
    action_cols = st.columns(4)
    actions = ["Rename", "Drop", "Create", "Binning"]

    for i, action in enumerate(actions):
        is_selected = st.session_state.get("col_op_action") == action
        if action_cols[i].button(action, use_container_width=True, key=f"col_op_btn_{action}", type="primary" if is_selected else "secondary"):
            st.session_state["col_op_action"] = action
            st.rerun()

    selected_action = st.session_state.get("col_op_action")
    if not selected_action:
        st.info("Select an operation above.")
        return

    st.divider()

    # RENAME COLUMNS
    if selected_action == "Rename":
        st.markdown("### Rename Columns")
        rename_df = pd.DataFrame({"Current Name": working_df.columns, "New Name": working_df.columns})
        edited_rename = st.data_editor(rename_df, use_container_width=True, hide_index=True, disabled=["Current Name"], key="rename_editor")

        renames = {}
        for _, row in edited_rename.iterrows():
            if row["Current Name"] != row["New Name"]:
                renames[row["Current Name"]] = row["New Name"]

        if renames:
            st.info(f"Will rename {len(renames)} column(s).")
            if st.button("Apply Renames", key="apply_renames"):
                checkpoint_state()
                working_df = working_df.rename(columns=renames)
                st.session_state["clean_df"] = working_df
                add_log("Rename Columns", {"renames": renames}, list(renames.values()), rows_affected={"columns_renamed": len(renames)})
                st.success(f"Renamed: {', '.join([f'{k} -> {v}' for k, v in renames.items()])}")
                st.rerun()
        else:
            st.caption("Change values in 'New Name' column to rename.")

    # DROP COLUMNS
    elif selected_action == "Drop":
        st.markdown("### Drop Columns")
        to_drop = st.multiselect("Select columns to remove", working_df.columns.tolist())

        if to_drop:
            st.warning(f"Warning: This will permanently remove {len(to_drop)} column(s).")
            if st.button("Drop Selected Columns", key="apply_drop"):
                checkpoint_state()
                working_df = working_df.drop(columns=to_drop)
                st.session_state["clean_df"] = working_df
                add_log("Drop Columns", "Permanently removed entirely from dataset", list(to_drop), rows_affected={"columns_deleted": len(to_drop)})
                st.success(f"Dropped: {', '.join(to_drop)}")

    # CREATE (VISUAL BUILDER)
    elif selected_action == "Create":
        st.markdown("### Visual Formula Builder")

        new_col_name = st.text_input("New Column Name", placeholder="e.g., Total_Value", key="formula_col_name")
        st.divider()

        builder_mode = st.radio(
            "Select Builder Mode",
            ["Basic Expression", "Function Builder", "Conditional (IF)", "Advanced (Click-to-Build)"],
            horizontal=True, key="formula_builder_mode"
        )

        formula_parts = []
        from utils import get_columns_by_type
        all_cols = working_df.columns.tolist()
        num_cols = get_columns_by_type(working_df, "numeric")

        if builder_mode == "Basic Expression":
            if not num_cols:
                st.warning("No numeric columns available for math operations.")
            else:
                c1, c2, c3 = st.columns(3)
                with c1:
                    col_a = st.selectbox("Column A", num_cols, key="basic_col_a")
                with c2:
                    op = st.selectbox("Operator", ["+", "-", "*", "/", "**", "%"], key="basic_op")
                with c3:
                    use_val = st.toggle("Use numeric value instead of Column B", key="basic_use_val")
                    if use_val:
                        val_b = st.number_input("Value", value=0.0, key="basic_val_b")
                        formula_parts = [col_a, op, str(val_b)]
                    else:
                        col_b = st.selectbox("Column B", num_cols, key="basic_col_b")
                        formula_parts = [col_a, op, col_b]

        elif builder_mode == "Function Builder":
            if not num_cols:
                st.warning("No numeric columns available for math functions.")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    func = st.selectbox("Function", ["log", "sqrt", "abs", "mean", "std"], key="func_select")
                with c2:
                    col_input = st.selectbox("Column Input", num_cols, key="func_col_input")
                formula_parts = [f"{func}(", col_input, ")"]

        elif builder_mode == "Conditional (IF)":
            st.markdown("**IF statement builder**")
            r1_c1, r1_c2, r1_c3 = st.columns(3)
            with r1_c1:
                if_col = st.selectbox("IF Column", all_cols, key="if_col")
            with r1_c2:
                if_op = st.selectbox("Condition", ["==", "!=", ">", "<", ">=", "<="], key="if_op")
            with r1_c3:
                if_val = st.text_input("Value", placeholder="e.g., 10 or 'Active'", key="if_val")
            r2_c1, r2_c2 = st.columns(2)
            with r2_c1:
                then_val = st.text_input("THEN (Result if TRUE)", placeholder="e.g., 1 or 'Yes'", key="if_then")
            with r2_c2:
                else_val = st.text_input("ELSE (Result if FALSE)", placeholder="e.g., 0 or 'No'", key="if_else")
            formula_parts = [f"if({if_col} {if_op} {if_val}, {then_val}, {else_val})"]

        elif builder_mode == "Advanced (Click-to-Build)":
            st.info("Click columns and operators to build your formula.")
            st.markdown("**Columns:**")
            cols_per_row = 6
            for i in range(0, len(all_cols), cols_per_row):
                chip_cols = st.columns(cols_per_row)
                for j, col_name in enumerate(all_cols[i:i+cols_per_row]):
                    if chip_cols[j].button(col_name, key=f"chip_{col_name}", use_container_width=True):
                        st.session_state["formula_input"] = st.session_state.get("formula_input", "") + f" {col_name} "
                        st.rerun()

            st.markdown("**Operators:**")
            op_cols = st.columns(8)
            ops = ["+", "-", "*", "/", "(", ")", ",", " "]
            for i, op in enumerate(ops):
                if op_cols[i].button(op, key=f"op_chip_{i}", use_container_width=True):
                    st.session_state["formula_input"] = st.session_state.get("formula_input", "") + op
                    st.rerun()

            formula_str_manual = st.text_input("Manual Formula", key="formula_input")
            if st.button("Clear Formula"):
                st.session_state["formula_input"] = ""
                st.rerun()

        # Formula Preview & Construction
        if builder_mode != "Advanced (Click-to-Build)":
            formula_str = " ".join(formula_parts)
            st.markdown(f"**Generated Formula:** `{formula_str}`")
        else:
            formula_str = st.session_state.get("formula_input", "")

        if formula_str and new_col_name:
            try:
                allowed_names = {
                    "log": np.log, "sqrt": np.sqrt, "abs": np.abs,
                    "mean": lambda x: x.mean(), "std": lambda x: x.std(),
                    "if": np.where, "np": np
                }

                sorted_cols = sorted(working_df.columns.tolist(), key=len, reverse=True)
                cleaned_formula = formula_str

                placeholders = {}
                for i, col in enumerate(sorted_cols):
                    placeholder = f"__COL_{i}__"
                    pattern = r'(?<![\w\'"])\b' + re.escape(col) + r'\b(?![\w\'"])'
                    if re.search(pattern, cleaned_formula):
                        cleaned_formula = re.sub(pattern, placeholder, cleaned_formula)
                        placeholders[placeholder] = f"working_df['{col}']"

                for ph, df_ref in placeholders.items():
                    cleaned_formula = cleaned_formula.replace(ph, df_ref)

                try:
                    res_preview = eval(cleaned_formula, {"__builtins__": None, "working_df": working_df.head(10)}, allowed_names)
                    st.divider()
                    st.markdown("**Preview (first 5 values):**")
                    if isinstance(res_preview, (pd.Series, np.ndarray)):
                        prev_df = pd.DataFrame({"Formula Result": res_preview[:5]})
                        st.table(prev_df)
                    else:
                        st.write(res_preview)

                    if st.button("✅ Apply & Create Column", key="apply_formula_visual", type="primary"):
                        checkpoint_state()
                        result = eval(cleaned_formula, {"__builtins__": None, "working_df": working_df}, allowed_names)
                        working_df[new_col_name] = result
                        st.session_state["clean_df"] = working_df
                        st.session_state["last_created_col"] = new_col_name
                        add_log("Create Column (Formula)", {"col_name": new_col_name, "formula": cleaned_formula}, [new_col_name], rows_affected={"columns_created": 1})
                        st.success(f"Created new column '{new_col_name}'")
                        if "formula_input" in st.session_state:
                            st.session_state["formula_input"] = ""
                        st.rerun()

                except (SyntaxError, ZeroDivisionError, NameError, TypeError) as e:
                    st.info(f"⏳ Formula incomplete or invalid for preview.")

            except Exception as e:
                st.error(f"⚠️ Oops! There was an error evaluating your formula. Please check your syntax and verify column names. (Details: {e})")

        # Show result overview if a column was just created
        if "last_created_col" in st.session_state:
            last_col = st.session_state["last_created_col"]
            if last_col in working_df.columns:
                st.divider()
                st.markdown(f"### Result Overview: `{last_col}`")
                st.write("Preview of the added data:")
                st.dataframe(working_df[[last_col]].head(10), use_container_width=True)
                if st.button("Dismiss Overview"):
                    del st.session_state["last_created_col"]
                    st.rerun()
        else:
            st.info("Complete the builder steps above to see a preview.")

    # BINNING (NUMERIC)
    elif selected_action == "Binning":
        st.markdown("### Numeric Binning")
        num_cols = [c for c in working_df.columns if pd.api.types.is_numeric_dtype(working_df[c])]

        if not num_cols:
            st.warning("No numeric columns available for binning.")
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            bin_col = st.selectbox("Select Column", num_cols, key="bin_col_select")
        with col2:
            n_bins = st.number_input("Number of Bins", min_value=2, max_value=20, value=5)
        with col3:
            strategy = st.selectbox("Strategy", ["Equal Width", "Quantile"], key="bin_strategy")

        if bin_col:
            new_bin_col = f"{bin_col}_Binned"
            try:
                if strategy == "Equal Width":
                    binned = pd.cut(working_df[bin_col], bins=n_bins)
                else:
                    binned = pd.qcut(working_df[bin_col], q=n_bins, duplicates='drop')

                st.markdown("**Preview (Distribution):**")
                counts = binned.value_counts().sort_index()
                counts.index = counts.index.astype(str)
                st.bar_chart(counts)

                if st.button("Apply Binning", key="apply_binning"):
                    checkpoint_state()
                    working_df[new_bin_col] = binned.astype(str)
                    st.session_state["clean_df"] = working_df
                    add_log("Numeric Binning", {"strategy": strategy, "bins": n_bins, "source_col": bin_col}, [new_bin_col], rows_affected={"columns_created": 1, "bins": len(counts)})
                    st.success(f"Created column '{new_bin_col}' with {len(counts)} unique bins.")
                    st.rerun()
            except Exception as e:
                st.error(f"⚠️ Could not create bins. Ensure the column has enough distinct numeric values. (Error: {e})")
