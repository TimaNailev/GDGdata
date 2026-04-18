import io
import pandas as pd
import streamlit as st


def show_data_validation(df: pd.DataFrame):
    st.subheader("Data Validation Engine")
    st.caption("Define rules to check data integrity. Violations will be collected without modifying the original data.")

    if "validation_rules" not in st.session_state:
        st.session_state["validation_rules"] = []

    all_cols = df.columns.tolist()

    # RULE DEFINITION UI
    with st.expander("➕ Add New Validation Rule", expanded=len(st.session_state["validation_rules"]) == 0):
        from utils import get_columns_by_type
        
        rule_type = st.selectbox("Rule Type", ["Numeric Range", "Allowed Categories", "Non-Null Constraint"], key="val_rule_type")
        
        # Determine valid columns for this rule type
        if rule_type == "Numeric Range":
            valid_cols = get_columns_by_type(df, "numeric")
        elif rule_type == "Allowed Categories":
            valid_cols = get_columns_by_type(df, "categorical")
        else:
            valid_cols = df.columns.tolist()
            
        if not valid_cols:
            st.warning(f"No appropriate columns found for a '{rule_type}' rule.")
            col_to_validate = None
        else:
            col_to_validate = st.selectbox("Select Column", valid_cols, key="val_col_select")
            
        new_rule = {"type": rule_type, "column": col_to_validate}
        can_add = col_to_validate is not None

        if rule_type == "Numeric Range" and col_to_validate:
            c1, c2 = st.columns(2)
            new_rule["min"] = c1.number_input("Minimum", value=0.0)
            new_rule["max"] = c2.number_input("Maximum", value=100.0)

        elif rule_type == "Allowed Categories":
            cat_input = st.text_input("Allowed values (comma separated)", placeholder="e.g., Active, Inactive, Pending")
            new_rule["allowed"] = [c.strip() for c in cat_input.split(",") if c.strip()]
            if not new_rule["allowed"]:
                can_add = False

        if st.button("Add Rule", use_container_width=True, disabled=not can_add):
            st.session_state["validation_rules"].append(new_rule)
            st.success(f"Added {rule_type} rule for '{col_to_validate}'")
            st.rerun()

    # CURRENT RULES LIST
    if st.session_state["validation_rules"]:
        st.markdown("### Active Rules")
        for i, rule in enumerate(st.session_state["validation_rules"]):
            c1, c2 = st.columns([4, 1])
            if rule["type"] == "Numeric Range":
                desc = f"**{rule['column']}**: Range [{rule['min']}, {rule['max']}]"
            elif rule["type"] == "Allowed Categories":
                desc = f"**{rule['column']}**: One of {rule['allowed']}"
            else:
                desc = f"**{rule['column']}**: Must not be null"

            c1.markdown(desc)
            if c2.button("🗑️", key=f"del_rule_{i}"):
                st.session_state["validation_rules"].pop(i)
                st.rerun()

        if st.button("Clear All Rules", type="secondary"):
            st.session_state["validation_rules"] = []
            st.rerun()

        st.divider()

        # VALIDATE BUTTON
        if st.button("🚀 Run Validation", type="primary", use_container_width=True):
            violations = []
            for rule in st.session_state["validation_rules"]:
                col = rule["column"]
                series = df[col]

                if rule["type"] == "Numeric Range":
                    mask = (series < rule["min"]) | (series > rule["max"])
                    issue = f"Outside range [{rule['min']}, {rule['max']}]"
                elif rule["type"] == "Allowed Categories":
                    # Case-insensitive check
                    allowed_lower = [str(a).lower() for a in rule["allowed"]]
                    series_val = series.astype(str).str.lower()
                    mask = (~series_val.isin(allowed_lower)) & (series.notna())
                    issue = f"Invalid category (not in {rule['allowed']})"
                elif rule["type"] == "Non-Null Constraint":
                    mask = series.isna()
                    issue = "Missing value (null)"

                violating_indices = df.index[mask].tolist()
                for idx in violating_indices:
                    violations.append({
                        "Row Index": idx, "Column": col,
                        "Issue": issue, "Current Value": str(series.loc[idx])
                    })

            if violations:
                v_df = pd.DataFrame(violations)
                st.session_state["last_validation_results"] = v_df
                st.error(f"Validation failed: Found {len(violations)} violations.")
            else:
                st.session_state["last_validation_results"] = None
                st.success("Validation passed! No violations found.")

    # RESULTS DISPLAY
    if "last_validation_results" in st.session_state and st.session_state["last_validation_results"] is not None:
        v_df = st.session_state["last_validation_results"]
        st.markdown("### Validation Violations")
        st.dataframe(v_df, use_container_width=True, hide_index=True)

        st.markdown("#### Export Results")
        e1, e2, e3 = st.columns(3)

        csv = v_df.to_csv(index=False).encode('utf-8')
        e1.download_button("Download CSV", csv, "violations.csv", "text/csv")

        json_str = v_df.to_json(orient="records", indent=4).encode('utf-8')
        e2.download_button("Download JSON", json_str, "violations.json", "application/json")

        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                v_df.to_excel(writer, sheet_name='Violations', index=False)
            e3.download_button("Download Excel", buffer.getvalue(), "violations.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception:
            e3.info("Excel export requires 'xlsxwriter'")

        st.divider()
        st.markdown("#### 🛠️ Actions")
        if st.button("🗑️ Remove Violations from Dataset", type="primary", use_container_width=True, help="Permanently delete all rows that failed validation"):
            from logger import add_log, checkpoint_state
            checkpoint_state()
            
            # Get unique indices to remove
            indices_to_remove = v_df["Row Index"].unique()
            rows_before = len(st.session_state["clean_df"])
            
            # Perform the drop
            st.session_state["clean_df"] = st.session_state["clean_df"].drop(index=indices_to_remove)
            rows_after = len(st.session_state["clean_df"])
            
            # Log the transformation
            add_log(
                "Remove Validation Violations",
                {"rules": st.session_state["validation_rules"], "total_violations": len(v_df)},
                list(v_df["Column"].unique()),
                rows_affected={"rows_deleted": rows_before - rows_after}
            )
            
            st.session_state["last_validation_results"] = None
            st.success(f"Successfully removed {rows_before - rows_after} rows containing validation violations.")
            st.rerun()
